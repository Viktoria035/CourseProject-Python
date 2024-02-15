
from gui.models import Player, PointsPerDay
from collections import defaultdict
import matplotlib.pyplot as plt

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

def get_registration_date(player: Player):
    return player.registration_date

def get_points_per_date_for_player(player: Player):
    points_per_day_res = {}
    points_per_days = PointsPerDay.objects.filter(player=player)
    for points_per_day in points_per_days:
        points_per_day_res[points_per_day.date] = points_per_day.points
    return points_per_day_res

def get_points_per_date_for_all_players():
    players = Player.objects.all()
    points_per_user_per_day = defaultdict(dict)
    for player in players:
        reg_date = get_registration_date(player)
        points_per_day = get_points_per_date_for_player(player)
        for day, points in points_per_day.items():
            days_since_registration = (day - reg_date).days
            points_per_user_per_day[player.user.username][days_since_registration] = points
    return points_per_user_per_day

def get_schedule_for_per_player():
    points_per_user_per_day = get_points_per_date_for_all_players()
    for username, points_per_day in points_per_user_per_day.items():
        sorted_days = sorted(points_per_day.keys())
        sorted_points = [points_per_day[day] for day in sorted_days]
        plt.plot(sorted_days, sorted_points, label=username)

    plt.xlabel('Days Since Registration')
    plt.ylabel('Points Earned')
    plt.title('Points Earned per Day Since Registration')
    plt.legend()
    plt.grid(True)

    plt.show()