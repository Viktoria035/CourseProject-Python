from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.urls import reverse
import logging
from gui.models import MultiPlayerSession, Player, Question, QuizAttempt, QuestionResponse, Answer, Quiz, QUESTION_TYPES
from django.template.loader import get_template

class QuizConsumer(AsyncWebsocketConsumer):
    """
    WebSocekt consumer is created when a player connect to a multiplayer session.
    It handles the communication between the players in the session.
    The consumer is responsible for:
      - sending the questions to the players;
      - receiving their answers;
      - sending the results from the quiz at the end of the play;
    """

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'quiz_{self.room_code}'

        # Add the player to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"Connected to room: {self.room_group_name}")

        # Get or create the multiplayer session and player
        try:
            self.multiplayer = await database_sync_to_async(self.get_multiplayer_session)()
        except MultiPlayerSession.DoesNotExist as e:
            print(f"Error: {e}")
            await self.close()
        self.player = await database_sync_to_async(lambda: Player.objects.get(user=self.scope['user']))()
        creator = await database_sync_to_async(lambda: self.multiplayer.creator)()
        
        # Create a quiz attempt for the player
        self.quiz = await database_sync_to_async(lambda: self.multiplayer.quiz)()
        quiz_attempt, _ = await database_sync_to_async(QuizAttempt.objects.get_or_create)(player=self.player, quiz=self.quiz)
        self.player.active_attempt = quiz_attempt
        await database_sync_to_async(self.player.save)()

        # Add player to the multiplayer session
        await database_sync_to_async(self.add_player_to_multiplayer)()

        if creator == self.player:
            # If the player is the creator, send the start game message
            await self.send(text_data=json.dumps({
                'type': 'start_game',
                'room_code': self.room_code
            }))
        else:
            current_question = await database_sync_to_async(lambda: self.multiplayer.current_question)()
            if current_question:
                question_serialized = self.serialize_question(current_question, self.quiz)
                total_players = await database_sync_to_async(self.multiplayer.players.count)()
                
                await self.send(text_data=json.dumps({
                'type': 'show_question',
                'question': question_serialized,
                'room_code': self.room_code,
                'total_players': total_players
            }))

    async def disconnect(self, close_code):
        # Remove player from the session
        await database_sync_to_async(self.multiplayer.players.remove)(self.player)
        await database_sync_to_async(self.multiplayer.save)()

        # Check if there are any players left in the session
        if await database_sync_to_async(self.multiplayer.players.count)() == 0:
            await database_sync_to_async(self.multiplayer.delete)()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"Disconnected from room: {self.room_group_name}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'start_game':
            await self.start_game()
        elif message_type == 'submit_answer':
            await self.submit_answer(text_data_json)

    async def start_game(self):
        try:
            if not self.multiplayer.started:
                await database_sync_to_async(setattr)(self.multiplayer, "started", True)
                await database_sync_to_async(self.multiplayer.save)()
                first_question = await database_sync_to_async(lambda: Question.objects.filter(quiz=self.quiz).first())()
                if not first_question:
                    self.close()
                    return
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'show_question',
                        'question_id': first_question.id
                    }
                )
            else:
                print("second start does not exist in real life bro")
        except Exception as e:
            print(f"Error in start_game: {e}")

    def serialize_question(self, question, quiz):
        return {
        'id': question.id,
        'text': question.question,
        'url': reverse('view_single_choice_question', kwargs={'quiz_id': quiz.id, 'question_id': question.id}) 
        if question.question_type == QUESTION_TYPES[0][0] 
        else reverse('view_multiple_choice_question', kwargs={'quiz_id': quiz.id, 'question_id': question.id}),
    }

    async def submit_answer(self, event):
        answer_ids = event.get('answer_ids', [])
        if not answer_ids:
            print("No answers provided")
            return
        answers = [await database_sync_to_async(lambda: Answer.objects.get(id=ans_id))() for ans_id in answer_ids]
        for answer in answers:
            question_response = await database_sync_to_async(lambda: QuestionResponse.objects.create(
                player=self.player,
                quiz=self.quiz,
                question=answer.question,
                answer=answer
            ))()
            await database_sync_to_async(lambda: self.player.active_attempt.responses.add(question_response))()
            if answer.is_correct:
                self.player.active_attempt.score += answer.points
                await database_sync_to_async(lambda: self.player.active_attempt.save())()
        
        await database_sync_to_async(lambda: self.player.save())()

        current_question = await database_sync_to_async(lambda: self.multiplayer.current_question)()        
        answered_count = 0
        total_players = await database_sync_to_async(lambda: self.multiplayer.players.count())()
        for player in await database_sync_to_async(lambda: list(self.multiplayer.players.all()))():
            for response in await database_sync_to_async(lambda: list(player.active_attempt.responses.all()))():
                if await database_sync_to_async(lambda: response.question)() == current_question:
                    answered_count += 1
                    break
        
        if answered_count == total_players:
            next_question = await database_sync_to_async(lambda: Question.objects.filter(quiz=self.quiz, id__gt=current_question.id).first())()
            if next_question:            
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'show_question',
                        'question_id': next_question.id
                    }
                )
            else:
                # If the current question is the last one and all players have answered, show the results
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'show_results'
                    }   
                )

    async def show_question(self, event):
        try:
            question_id = event['question_id']
            question = await database_sync_to_async(lambda: Question.objects.get(id=question_id))()
            if not question:
                print("No question found")
                return
            
            await database_sync_to_async(setattr)(self.multiplayer, "current_question", question)
            await database_sync_to_async(self.multiplayer.save)()
            question_serialized = self.serialize_question(question, self.quiz)
            await self.send(text_data=json.dumps(
                {
                    'type': 'show_question',
                    'question': question_serialized,
                    'room_code': self.room_code
                }
            ))
        except Exception as e:
            print(f"Error in show_question: {e}")

    async def show_results(self, event):
        players = await database_sync_to_async(lambda: list(self.multiplayer.players.all()))()
        if not players:
            print("No players found")
            return
        results = []
        for player in players:
            results.append(
                {
                'player_username': await database_sync_to_async(lambda: player.user.username)(),
                'score': await database_sync_to_async(lambda: player.active_attempt.score)()
                }
            )
            player.score += player.active_attempt.score
            # May be unnecessary now, but just in case fot the future
            # await database_sync_to_async(lambda: player.active_attempt.responses.clear())()
            # player.active_attempt.score = 0
            player.active_attempt = None
            await database_sync_to_async(lambda: player.save())()

        results.sort(key=lambda x: x['score'], reverse=True)
        await self.send(text_data=json.dumps({
            'type': 'show_results',
            'results': results
        }))

    def add_player_to_multiplayer(self):
        self.multiplayer.players.add(self.player)
        self.multiplayer.save()

    def get_multiplayer_session(self):
        return MultiPlayerSession.objects.get(room_code=self.room_code)
