from channels.db import database_sync_to_async
from gui.models import QuizAttempt, Player, MultiPlayerSession, Question, Answer, QuestionResponse, Quiz, QuestionType
from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.urls import reverse

class QuizConsumer(AsyncJsonWebsocketConsumer):
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

        try:
            self.multiplayer = await self.get_multiplayer_session()
            self.player = await self.get_player()
            self.quiz = await database_sync_to_async(lambda: self.multiplayer.quiz)()
        except MultiPlayerSession.DoesNotExist or Player.DoesNotExist or Quiz.DoesNotExist:
            print("Session or player or quiz does not exist")
            await self.close()
            return
        
        await self.create_or_update_quiz_attempt()
        await self.add_player_to_session()

        if await self.is_creator() or not self.multiplayer.started:
            await self.send_start_game_massage()
        else:
            if self.multiplayer.started:
                await self.send_question_if_game_already_started()

    async def disconnect(self, close_code):
        await self.remove_player_from_session()

        if await database_sync_to_async(self.multiplayer.players.count)() == 0:
            await self.stop_session()

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
                await self.set_session_started()
                await self.send_first_question()
            else:
                print("second start does not exist in real life bro")
        except Exception as e:
            print(f"Error starting game: {e}")

    async def submit_answer(self, event):
        answer_ids = event.get('answer_ids', [])
        if not answer_ids:
            print("No answers provided")
            return

        try:
            answers = await self.get_answers(answer_ids)
            print("before")
            await self.create_question_response_and_update_score(answers)

            if await self.check_if_all_players_have_answered():
                print("after")
                next_question = await self.get_next_question()
                if next_question:
                    await self.send_next_question(next_question)
                else:
                    await self.send_results()
        except Exception as e:
            print(f"Error submitting answer: {e}")
            
    def serialize_question(self, question, quiz):
        return {
        'id': question.id,
        'text': question.question,
        'url': reverse('view_single_choice_question', kwargs={'quiz_id': quiz.id, 'question_id': question.id}) 
        if question.question_type == QuestionType.SINGLE_CHOICE.value  
        else reverse('view_multiple_choice_question', kwargs={'quiz_id': quiz.id, 'question_id': question.id}),
    }

    async def show_question(self, event):
        try:
            question_id = event.get('question_id')
            if not question_id:
                print("No question ID provided")
                return
            question = await database_sync_to_async(Question.objects.get)(id=question_id)
            await self.set_current_question(question)
            question_serialized = self.serialize_question(question, self.quiz)
            await self.send_question_to_group(question_serialized)
        except Exception as e:
            print(f"Error showing question: {e}")

    async def show_results(self, event):
        players = await self.get_all_players()
        if not players:
            print("No players found")
            return
        results = await self.get_results_for_all_players(players)
        await self.send_results_to_group(results)

    async def get_multiplayer_session(self):
        return await database_sync_to_async(MultiPlayerSession.objects.get)(room_code=self.room_code)

    async def create_or_update_quiz_attempt(self):
        quiz_attempt, _ = await database_sync_to_async(QuizAttempt.objects.get_or_create)(player=self.player, quiz=self.quiz)
        self.player.active_attempt = quiz_attempt
        await database_sync_to_async(self.player.save)()

    async def add_player_to_session(self):
        # Add player to the session
        await database_sync_to_async(self.multiplayer.players.add)(self.player)
        await database_sync_to_async(self.multiplayer.save)()

    async def get_player(self):
        return await database_sync_to_async(Player.objects.get)(user=self.scope['user'])

    async def is_creator(self):
        creator = await database_sync_to_async(lambda: self.multiplayer.creator)()
        return creator == self.player

    async def send_start_game_massage(self):
        await self.send(text_data=json.dumps({
                'type': 'start_game',
                'room_code': self.room_code
            }))
        
    async def send_question_if_game_already_started(self):
        current_question = await database_sync_to_async(lambda: self.multiplayer.current_question)()
        if current_question:
            question_serialized = self.serialize_question(current_question, self.quiz)
                        
            await self.send(text_data=json.dumps({
                'type': 'show_question',
                'question': question_serialized,
            }))

    async def remove_player_from_session(self):
        # Remove player from the session
        await database_sync_to_async(self.multiplayer.players.remove)(self.player)
        await database_sync_to_async(self.multiplayer.save)()

    async def stop_session(self):
        await database_sync_to_async(setattr)(self.multiplayer, "active", False)
        await database_sync_to_async(setattr)(self.multiplayer, "started", False)
        await database_sync_to_async(self.multiplayer.save)()

    async def set_session_started(self):
        await database_sync_to_async(setattr)(self.multiplayer, "started", True)
        await database_sync_to_async(self.multiplayer.save)()

    async def send_first_question(self):
        first_question = await database_sync_to_async(Question.objects.filter(quiz=self.quiz).first)()
        if not first_question:
            self.close()
            return
                    
        await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'show_question',
                'question_id': first_question.id
            })

    async def set_current_question(self, question):
        await database_sync_to_async(setattr)(self.multiplayer, "current_question", question)
        await database_sync_to_async(self.multiplayer.save)()

    async def send_question_to_group(self, question_serialized):
        await self.send(text_data=json.dumps({
                'type': 'show_question',
                'question': question_serialized
            }))

    async def get_all_players(self):
        return await database_sync_to_async(lambda: list(self.multiplayer.players.all()))()

    async def get_results_for_all_players(self, players):
        results = []
        for player in players:
            results.append({
                'player_username': await database_sync_to_async(lambda: player.user.username)(),
                'score': await database_sync_to_async(lambda: player.active_attempt.score)()
            })
            player.score += player.active_attempt.score
            # May be unnecessary now, but just in case fot the future
            # await database_sync_to_async(lambda: player.active_attempt.responses.clear())()
            # player.active_attempt.score = 0
            player.active_attempt = None
            await database_sync_to_async(player.save)()

        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    async def send_results_to_group(self, results):
        await self.send(text_data=json.dumps({
                'type': 'show_results',
                'results': results
        }))

    async def get_answers(self, answer_ids):
        answers = [await database_sync_to_async(Answer.objects.get)(id=ans_id) for ans_id in answer_ids]
        return answers

    async def create_and_add_question_response(self, answer):
        question_response = await database_sync_to_async(lambda: QuestionResponse.objects.create(
                    player=self.player,
                    quiz=self.quiz,
                    question=answer.question,
                    answer=answer
                ))()
        await database_sync_to_async(self.player.active_attempt.responses.add)(question_response)

    async def update_score_if_answer_is_correct(self, answer):
        if answer.is_correct:
            self.player.active_attempt.score += answer.points
            print(f"Score: {self.player.active_attempt.score}")
            await database_sync_to_async(self.player.active_attempt.save)()
            
    async def check_if_all_players_have_answered(self):
        answered_count = 0
        current_question = await database_sync_to_async(lambda: self.multiplayer.current_question)()
        players = await database_sync_to_async(lambda: list(self.multiplayer.players.all()))()
        total_players = len(players)

        for player in players:
            responses = await database_sync_to_async(lambda: list(player.active_attempt.responses.all()))()
            for response in responses:
                if await database_sync_to_async(lambda: response.question)() == current_question:
                    answered_count += 1
                    break

        return answered_count == total_players

    async def get_next_question(self):
        return await database_sync_to_async(lambda: Question.objects.filter(quiz=self.quiz, id__gt=self.multiplayer.current_question.id).first())()

    async def send_next_question(self, next_question):
        await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'show_question',
                'question_id': next_question.id
            })

    async def send_results(self):
        # If the current question is the last one and all players have answered, show the results
        await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'show_results'
            })


    async def create_question_response_and_update_score(self, answers):
        print("in")
        for answer in answers:
            await self.create_and_add_question_response(answer)
            await self.update_score_if_answer_is_correct(answer)
        
        await database_sync_to_async(self.player.save)()
