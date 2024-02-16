
from gui.models import Player, PointsPerDay
from collections import defaultdict
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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
    if 0 <= player.score <= 10:
        player.level = 'Beginner'
    elif 10 < player.score <= 20:
        player.level = 'Medium'
    elif 20 < player.score <= 30:
        player.level = 'Good'
    elif 30 < player.score <= 40:
        player.level = 'Very good'
    elif 40 < player.score <= 50:
        player.level = 'Impressive'
    elif 50 < player.score <= 60:
        player.level = 'Fighting for top'
    else:
        player.level = 'Master'


# def get_registration_date(player: Player):
#     return player.registration_date

# def get_points_per_date_for_player(player: Player):
#     points_per_day_res = {}
#     points_per_days = PointsPerDay.objects.filter(player=player)
#     for points_per_day in points_per_days:
#         points_per_day_res[points_per_day.date] = points_per_day.points
#     return points_per_day_res

# def get_points_per_date_for_all_players():
#     players = Player.objects.all()
#     points_per_user_per_day = defaultdict(dict)
#     for player in players:
#         reg_date = get_registration_date(player)
#         points_per_day = get_points_per_date_for_player(player)
#         for day, points in points_per_day.items():
#             days_since_registration = (day - reg_date).days
#             points_per_user_per_day[player.user.username][days_since_registration] = points
#     return points_per_user_per_day

# def get_schedule_for_per_player():
#     points_per_user_per_day = get_points_per_date_for_all_players()
#     for username, points_per_day in points_per_user_per_day.items():
#         sorted_days = sorted(points_per_day.keys())
#         sorted_points = [points_per_day[day] for day in sorted_days]
#         plt.plot(sorted_days, sorted_points, label=username)

#     plt.xlabel('Days Since Registration')
#     plt.ylabel('Points Earned')
#     plt.title('Points Earned per Day Since Registration')
#     plt.legend()
#     plt.grid(True)

#     plt.show()


def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph

def get_plot_for_per_player_since_registration(x, y):
    plt.switch_backend('AGG')
    plt.figure(figsize=(10, 5))
    plt.title('Points Earned per Day Since Registration', fontsize=25, fontname="Baskerville Old Face")
    plt.bar(x, y, color='orange', edgecolor='black')
    plt.xticks(rotation=45)
    plt.xlabel('Days Since Registration', fontsize=15, fontname="Baskerville Old Face")
    plt.ylabel('Points Earned', fontsize=15, fontname="Baskerville Old Face")
    plt.tight_layout()
    graph = get_graph()
    return graph

def get_plot_for_each_quiz_score(x, y):
    plt.switch_backend('AGG')
    plt.figure(figsize=(10, 5))
    plt.title('Points earned from each quiz', fontsize=25, fontname="Baskerville Old Face")
    plt.scatter(x, y, c='orange')
    plt.xticks(rotation=45)
    plt.xlabel('Quizzes', fontsize=15, fontname="Baskerville Old Face")
    plt.ylabel('Points earned', fontsize=15, fontname="Baskerville Old Face")
    plt.tight_layout()
    plt.grid(True)
    graph = get_graph()
    return graph