from django.test import TestCase
from .models import Player, PointsPerDay
from app.functions import get_player_rank_in_leaderboard, change_player_level_by_score
from django.contrib.auth.models import User
# Create your tests here.


class PlayerLevelTestCase(TestCase):

    def test_begginer_level(self):
        player = Player(score=5)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Beginner')

    def test_medium_level(self):
        player = Player(score=15)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Medium')

    def test_good_level(self):
        player = Player(score=25)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Good')

    def test_very_good_level(self):
        player = Player(score=35)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Very good')

    def test_impressive_level(self):
        player = Player(score=45)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Impressive')

    def test_fighting_for_the_top_level(self):
        player = Player(score=55)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Fighting for the top')

    def test_master_level(self):
        player = Player(score=65)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Master')

    def test_noob_level(self):
        player = Player(score=-5)
        change_player_level_by_score(player)
        self.assertEqual(player.level, 'Noob')


class PlayerRankTestCase(TestCase):
    
    def set_up(self):
        user1 = User.objects.create(username='user1')
        user2 = User.objects.create(username='user2')
        user3 = User.objects.create(username='user3')
        user4 = User.objects.create(username='user4')
        user5 = User.objects.create(username='user5')
        user6 = User.objects.create(username='user6')
        Player.objects.create(user=user1, score=100)
        Player.objects.create(user=user2, score=80)
        Player.objects.create(user=user3, score=60)
        Player.objects.create(user=user4, score=40)
        Player.objects.create(user=user5, score=20)
        Player.objects.create(user=user6, score=-2)

    def test_get_rank_first_place(self):
        player = Player.objects.get(score=100)
        rank = get_player_rank_in_leaderboard(player)
        self.assertEqual(player.rank, 1)

    def test_get_rank_middle_place(self):
        player = Player.objects.get(score=60)
        rank = get_player_rank_in_leaderboard(player)
        self.assertEqual(player.rank, 3)

    def test_get_rank_last_place(self):
        player = Player.objects.get(score=20)
        rank = get_player_rank_in_leaderboard(player)
        self.assertEqual(player.rank, 5)

    def test_get_rank_with_negative_score(self):
        player = Player.objects.get(score=-2)
        get_player_rank_in_leaderboard(player)
        self.assertEqual(player.rank, 6)

    def test_player_not_in_leaderboard(self):
        new_user = User.objects.create(username='new_user')
        player = Player.objects.create(user=new_user, score=70)
        rank = get_player_rank_in_leaderboard(player)
        self.assertEqual(player.rank, 3)