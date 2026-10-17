from html import escape

def format_report(data):
    rows = ['<h2>FPL Gameweek {}</h2>'.format(data['gameweek'])]
    for player in data['players']:
        rows.append('<p>{}: {} points</p>'.format(escape(player['name']), player['points']))
    return '\n'.join(rows)
