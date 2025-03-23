from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.urls import reverse

from gui.models import MultiPlayerSession, Player, Question, QuizAttempt, QuestionResponse, Answer, Quiz

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
        self.multiplayer = await database_sync_to_async(MultiPlayerSession.objects.get)(room_code=self.room_code)
        self.player = await database_sync_to_async(Player.objects.get)(user=self.scope['user'])

        # Create a quiz attempt for the player
        self.quiz = await database_sync_to_async(lambda: self.multiplayer.quiz)()
        quiz_attempt, _ = await database_sync_to_async(QuizAttempt.objects.get_or_create)(player=self.player, quiz=self.quiz)
        self.player.active_attempt = quiz_attempt
        await database_sync_to_async(self.player.save)()

        # Add player to the multiplayer session
        await database_sync_to_async(self.multiplayer.players.add)(self.player)
        await database_sync_to_async(self.multiplayer.save)()

        # Notify other players that a new player has joined
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',
        #         'message': f'{await database_sync_to_async(lambda: self.player.user.username)()} has joined the game'
        #     }
        # )

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
        username = text_data_json['username']

        print(f"Received message: {text_data_json}")

        if message_type == 'join':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': f'{username} has joined the join game'
                }
            )
        elif message_type == 'start_game':
            await self.start_game()
        elif message_type == 'submit_answer':
            await self.submit_answer(text_data_json['answers_ids'])

    async def start_game(self):
        first_question = await database_sync_to_async(lambda: Question.objects.filter(quiz=self.quiz).first())()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'show_question',
                'question': self.serialize_question(first_question, self.quiz),
                'room_code': self.room_code
            }
        )

    async def submit_answer(self, answers_ids):
        answers = [await database_sync_to_async(Answer.objects.get)(id=ans_id) for ans_id in answers_ids]
        for answer in answers:
            question_response = await database_sync_to_async(QuestionResponse.objects.create)(
                player=self.player,
                quiz=self.quiz,
                question=answer.question,
                answer=answer
            )
            await database_sync_to_async(self.player.active_attempt.responses.add)(question_response)
            if answer.is_correct:
                self.player.active_attempt.score += answer.points
                await database_sync_to_async(self.player.active_attempt.save)()

        await database_sync_to_async(self.player.save)()

        # Check if all players have answered the current question
        current_question = answers[0].question
        answered_count = 0
        for player in await database_sync_to_async(self.multiplayer.players.all)():
            for response in player.active_attempt.responses.all():
                if response.question == current_question:
                    answered_count += 1

        if answered_count == await database_sync_to_async(self.multiplayer.players.count)():
            next_question = await database_sync_to_async(Question.objects.filter)(quiz=self.quiz, id__gt=current_question.id).first()
            if next_question:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'show_question',
                        'question': self.serialize_question(next_question)
                    }
                )
            else:
                results = []
                for player in await database_sync_to_async(self.multiplayer.players.all)():
                    results.append({
                        'player': player.user.username,
                        'score': player.active_attempt.score
                    })
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'show_results',
                        'results': results
                    }
                )

    def serialize_question(self, question, quiz):
        return {
        'id': question.id,
        'text': question.question,
        'url': reverse('view_single_choice_question', kwargs={'quiz_id': quiz.id, 'question_id': question.id}) 
        if question.question_type == 'single choice' 
        else reverse('view_multiple_choice_question', kwargs={'quiz_id': quiz.id, 'question_id': question.id}),
        'open_in_new_tab': True
    }

    async def show_question(self, event):
        await self.send(text_data=json.dumps({
            'type': 'show_question',
            'question': event['question'],
            'room_code': event['room_code']
        }))

    async def show_results(self, event):
        await self.send(text_data=json.dumps({
            'type': 'show_results',
            'results': event['results']
        }))

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
        print(f"Sent message: {message}")