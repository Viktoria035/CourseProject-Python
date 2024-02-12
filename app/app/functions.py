
from gui.models import Player
from django.db.models import F

def get_player_rank_in_leaderboard(player: Player):
    leaderboard = Player.objects.all().order_by('-score')

    rank = 1
    for p in leaderboard:
        if p == player:
            player.rank = rank
            break
        rank += 1
    return None

def change_player_level_by_score(player: Player):
    if player.score <= 0 and player.score >= 10:
        player.level = 'Beginner'
    elif player.score > 10 and player.score <= 20:
        player.level = 'Medium'
    elif player.score > 20 and player.score <= 30:
        player.level = 'Good'
    elif player.score > 30 and player.score <= 40:
        player.level = 'Very good'
    elif player.score > 40 and player.score <= 50:
        player.level = 'Impresive'
    elif player.score > 50 and player.score <= 60:
        player.level = 'Fighting for top'
    elif player.score >= 100:
        player.level = 'Master'