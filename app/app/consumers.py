from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

from gui.models import MultiPlayerSession, Player, Question, QuizAttempt, QuestionResponse, Answer



class MultiplayerQuizGame(WebsocketConsumer):
    def connect(self):
        """In this function, we get the room name from the URL route parameters, 
        and then we use it to get the MultiPlayerSession object from the database.
        We also get the first question of the quiz and the room group name. 
        We then add the user to the group and accept the connection."""

        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.multiplayer = MultiPlayerSession.objects.get(room_code=self.room_name)
        self.question = Question.objects.filter(id=1, quiz=self.multiplayer.quiz).first()
        self.room_group_name = 'room_%s' %  self.room_name
        print(self.room_group_name) 
        player = Player.objects.get(user=self.scope['user'])
        
        quiz_attempt = QuizAttempt(player=Player.objects.get(user=self.scope['user']), quiz=self.multiplayer.quiz)
        quiz_attempt.save()
        
        player.active_attempt = quiz_attempt
        player.save()
        
        self.multiplayer.players.add(player)
        self.multiplayer.save()

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        self.accept()

        
    def disconnect(self):
        """In this function, we remove the user from the group and delete the MultiPlayerSession object if there is only one player left."""
        if len(self.multiplayer.players) <= 1:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
            self.multiplayer.delete()
        else:
            self.multiplayer.players.remove(self.scope['user'])
            self.multiplayer.save()

        
    def receive(self , payload):
        """In this function, we have a few different cases.
        If the action is start_game and the player is the creator, we send the question to the group.
        If the action is submit_answer, we save the player's response and check if all players have answered.
        If all players have answered, we send the next question to the group.
        If there are no more questions, we send the results to the group."""

        print(payload)
        player = Player.objects.get(user=self.scope['user'])

        if payload['action'] == 'start_game' and player == self.multiplayer.creator:
            # Creator starts the game
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,{
                    'action' : 'question',
                    'game_status' : 'running',
                    'payload' : self.question
                }
            )
        elif payload['action'] == 'submit_answer':
            # Player submits answer
            answer_responses_ids = payload['answers_ids']

            answers = [Answer.objects.filter(question=self.question, id=answer_response_id).first() for answer_response_id in answer_responses_ids]
            for answer in answers:
                question_response = QuestionResponse(
                    player=player,
                    quiz=self.multiplayer.quiz,
                    question=self.question,
                    answer=answer,
                )
                question_response.save()
                player.active_attempt.responses.add(question_response)
                
                if answer.is_correct:
                    player.active_attempt.score += answer.points
                    player.active_attempt.save()
            player.save()

        next_question = Question.objects.filter(quiz=self.multiplayer.quiz, id__gt=self.question.id).first()
        
        if next_question:
            answered_count = 0
            for player in self.multiplayer.players:
                for response in player.active_attempt.responses:
                    if response.question == self.question:
                        answered_count += 1

            if next_question and answered_count == len(self.multiplayer.players):
                # All players have answered
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,{
                        'action' : 'question',
                        'game_status' : 'running',
                        'payload' : next_question
                    }
                )
        else:
            results = []
            for player in self.multiplayer.players:
                results.append({
                    "player": player.user.username,
                    "score": player.active_attempt.score
                })
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,{
                    'action' : 'question',
                    'game_status' : 'ended',
                    'results' : results
                }
            )
