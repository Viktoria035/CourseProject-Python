
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

def change_player_level_by_score(player: Player):
    if player.score < 0:
        player.level = 'Noob'
    elif 0 <= player.score <= 10:
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
        player.level = 'Fighting for the top'
    else:
        player.level = 'Master'

def get_graph():
    """Function that generates a graph using matplotlip, save it as a PNG in memory, encode it into 
    base64 format, and then return the base64 encoded string representation of the image."""

    buffer = BytesIO() # creates an in-memory buffer
    plt.savefig(buffer, format='png') # saves the current matplotlib figure to the buffer in PNG format
    buffer.seek(0) # moves the pointer of the buffer back to the beginning, to read it from the start.
    image_png = buffer.getvalue() # reads the content of the buffer
    graph = base64.b64encode(image_png) # encodes the content of the buffer into base64 format
    graph = graph.decode('utf-8') # converts the base64 encoded bytes to a UTF-8 string representation
    buffer.close() # closes the buffer to free up system resources
    return graph

def get_plot_for_per_player_since_registration(x, y):
    plt.switch_backend('AGG')  # switches the backend of matplotlib to 'AGG', which is a non-interactive backend that is often used when generating plots without displaying them directly    plt.figure(figsize=(10, 5))
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