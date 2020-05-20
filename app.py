from flask import Flask, render_template, redirect, url_for, request
import requests, json, os
from markupsafe import escape
from exports import championIdMap, queueTypes, itemMap
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # to suppress 'QApplication was not created in the main() thread' warning
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from dotenv import load_dotenv
load_dotenv()

summonerId = [] # global because used in two different functions that are being used in maps

summonerName = 'a'

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.errorhandler(500)
def internalError(error):
    return render_template('error.html', summonerName=summonerName)

@app.route('/home')
def redirectHome():
    return redirect(url_for('home'))

@app.route('/profile', methods=['POST'])
def profile():
    global summonerName # global so it can be used in internalError handling
    summonerName = request.form['summonerName']
    return redirect(url_for('showProfile', name=summonerName))

@app.route('/profile/<name>')
def showProfile(name):
    # variables declared locally for performance improvement
    API = f"?api_key={os.getenv('API_KEY')}"
    SUMMONER_URL = 'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/'
    PROFILE_ICON = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/profileicon/'
    RANKED_URL = 'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/'
    MASTERY_URL = 'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/'
    MATCHLIST_URL = 'https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/'

    # local functions that are called inside loops
    getMasteryData = getMasteryDataGlobal
    getMatchData = getMatchDataGlobal

    # get summoner info
    res = requests.get(f"{SUMMONER_URL}{escape(name)}{API}")
    summonerData = json.loads(res.text)
    
    summonerId.append(summonerData['id'])

    imgLink = f"{PROFILE_ICON}{str(summonerData['profileIconId'])}.png"
    summonerLevel = summonerData['summonerLevel']

    # get ranked info
    res = requests.get(f"{RANKED_URL}{str(summonerData['id'])}{API}")
    parsedRankedDataList = json.loads(res.text)

    rankedData = {'rank': '', 'numWins': 0, 'numLosses': 0, 'queueType': ''}
    if parsedRankedDataList:
        parsedRankedData = parsedRankedDataList[0]
        rankedData['rank'] = f"{parsedRankedData['tier']} {parsedRankedData['rank']}"
        rankedData['numWins'] = parsedRankedData['wins']
        rankedData['numLosses'] = parsedRankedData['losses']
        rankedData['queueType'] = parsedRankedData['queueType']

    # get champion mastery info
    res = requests.get(f"{MASTERY_URL}{str(summonerData['id'])}{API}")
    parsedMasteryData = json.loads(res.text)

    masteryData = list(map(getMasteryData, parsedMasteryData[:3]))

    # get match history
    res = requests.get(f"{MATCHLIST_URL}{str(summonerData['accountId'])}{API}")
    parsedMatchList = json.loads(res.text)

    # get individual game info
    matchList = list(map(getMatchData, parsedMatchList['matches'][:5]))

    return render_template('profile.html', summonerName=summonerData['name'], imgLink=imgLink, summonerLevel=summonerLevel, rankedData=rankedData, masteryData=masteryData, matchList=matchList)

def getMasteryDataGlobal(champion):
    CHAMPION_LOADING_ICON = 'http://ddragon.leagueoflegends.com/cdn/img/champion/loading/'
    return {'championIcon': f"{CHAMPION_LOADING_ICON}{championIdMap[champion['championId']]}_0.jpg", 'championName': championIdMap[champion['championId']], 'level': champion['championLevel'], 'points': champion['championPoints']}
    
def getMatchDataGlobal(parsedMatch):
    API = f"?api_key={os.getenv('API_KEY')}"
    MATCH_URL = 'https://na1.api.riotgames.com/lol/match/v4/matches/'
    CHAMPION_SQUARE_ICON = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/champion/'
    ITEM_URL = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/item/'
    res = requests.get(f"{MATCH_URL}{str(parsedMatch['gameId'])}{API}")
    matchData = json.loads(res.text)

    # get type of game (e.g. ranked, normal, custom)
    gameType = ''
    queueId = parsedMatch['queue']
    if queueId == 0:
        gameType = 'Custom'
    else:
        # binary search
        l, r = 0, len(queueTypes)-1
        while l + 1 < r:
            mid = l + (r - l) // 2
            if queueTypes[mid]['queueId'] == queueId:
                gameType = queueTypes[mid]['description'][:-6]
                break
            if queueTypes[mid]['queueId'] < queueId:
                l = mid
            else:
                r = mid
        if queueTypes[l]['queueId'] == queueId:
            gameType = queueTypes[l]['description'][:-6]
        elif queueTypes[r]['queueId'] == queueId:
            gameType = queueTypes[r]['description'][:-6]

    # blue and red team info
    blueTeamMatchData = matchData['teams'][0] # teamId = 100
    blueTeamKills = 0
    blueTeamFirstDragon = blueTeamMatchData['firstDragon']
    blueTeamDragonKills = blueTeamMatchData['dragonKills']
    blueTeamFirstRiftHerald = blueTeamMatchData['firstRiftHerald']
    blueTeamRiftHeraldKills = blueTeamMatchData['riftHeraldKills']
    blueTeamFirstBaron = blueTeamMatchData['firstBaron']
    blueTeamBaronKills = blueTeamMatchData['baronKills']
    blueTeamFirstBlood = blueTeamMatchData['firstBlood']
    blueTeamFirstTower = blueTeamMatchData['firstTower']
    blueTeamTowerKills = blueTeamMatchData['towerKills']
    blueTeamTotalWardsPlaced = 0
    redTeamMatchData = matchData['teams'][1] # teamId = 200
    redTeamKills = 0
    redTeamFirstDragon = redTeamMatchData['firstDragon']
    redTeamDragonKills = redTeamMatchData['dragonKills']
    redTeamFirstRiftHerald = redTeamMatchData['firstRiftHerald']
    redTeamRiftHeraldKills = redTeamMatchData['riftHeraldKills']
    redTeamFirstBaron = redTeamMatchData['firstBaron']
    redTeamBaronKills = redTeamMatchData['baronKills']
    redTeamFirstBlood = redTeamMatchData['firstBlood']
    redTeamFirstTower = redTeamMatchData['firstTower']
    redTeamTowerKills = redTeamMatchData['towerKills']
    redTeamTotalWardsPlaced = 0

    # for plotting blue and red team damage
    labels = []
    values = []

    kills = 0
    deaths = 0
    assists = 0
    damage = 0
    win = True
    wardsPlaced = 0
    side = 'Blue'
    avgCsPerMin = 0
    totalCS = 0
    gameLength = ''
    item0 = ''
    item1 = ''
    item2 = ''
    item3 = ''
    item4 = ''
    item5 = ''
    item6 = ''
    players = {}
    for i in range(10):
        # get stats for all players
        playerStats = matchData['participants'][i]['stats']
        playerIdentity = matchData['participantIdentities'][i]['player']
        players[i] = {'summonerName': playerIdentity['summonerName'], 'champion': championIdMap[matchData['participants'][i]['championId']], 'kills': playerStats['kills'], 'deaths': playerStats['deaths'], 'assists': playerStats['assists'], 'cs': playerStats['totalMinionsKilled'] + playerStats['neutralMinionsKilled']}
            
        if i < 5:
            blueTeamKills += playerStats['kills']
            blueTeamTotalWardsPlaced += playerStats['wardsPlaced']
        else:
            redTeamKills += playerStats['kills']
            redTeamTotalWardsPlaced += playerStats['wardsPlaced']
            
        # get player stats
        if summonerId[0] == playerIdentity['summonerId']:
            kills = playerStats['kills']
            deaths = playerStats['deaths']
            assists = playerStats['assists']
            damage = playerStats['totalDamageDealtToChampions']
            win = playerStats['win']
            wardsPlaced = playerStats['wardsPlaced']
            if i > 5:
                side = 'Red'
            avgCsPerMin = int((playerStats['totalMinionsKilled'] + playerStats['neutralMinionsKilled']) // (matchData['gameDuration'] / 60))
            totalCS = players[i]['cs']
            minutes = matchData['gameDuration'] // 60
            seconds = matchData['gameDuration'] - (minutes * 60)
            if seconds < 10:
                gameLength = str(minutes) + ':0' + str(seconds)
            else:
                gameLength = str(minutes) + ':' + str(seconds)
            if playerStats['item0'] != 0:
                item0 = itemMap['data'][str(playerStats['item0'])]['image']['full']
            if playerStats['item1'] != 0:
                item1 = itemMap['data'][str(playerStats['item1'])]['image']['full']
            if playerStats['item2'] != 0:
                item2 = itemMap['data'][str(playerStats['item2'])]['image']['full']
            if playerStats['item3'] != 0:
                item3 = itemMap['data'][str(playerStats['item3'])]['image']['full']
            if playerStats['item4'] != 0:
                item4 = itemMap['data'][str(playerStats['item4'])]['image']['full']
            if playerStats['item5'] != 0:
                item5 = itemMap['data'][str(playerStats['item5'])]['image']['full']
            if playerStats['item6'] != 0:
                item6 = itemMap['data'][str(playerStats['item6'])]['image']['full']
                    
        labels.append(players[i]['champion'])
        values.append(playerStats['totalDamageDealtToChampions'])

    # create plot for blue team
    offset_image = offsetImageGlobal
    fig1, ax1 = plt.subplots(figsize=(3,3))
    ax1.bar(range(5), values[:5], align='center')
    ax1.set_title('Damage Dealt to Champions', color='white')
    ax1.set_xticks(range(5))
    # set pictures as labels
    ax1.set_xticklabels([' ', ' ', ' ', ' ', ' '])
    ax1.tick_params(axis='x', which='major', pad=26)
    ax1.set_yticks([])
    for i, c in enumerate(labels[:5]):
        offset_image(i, c, ax1)
    # hide border
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    # add text to bars
    for i, v in enumerate(values[:5]):
        ax1.text(i, v, str(v), ha='center', color='white')
    fig1.tight_layout()
    fig1.savefig(os.path.join('static/images/graphs', f"blueTeam{str(parsedMatch['gameId'])}.png"), transparent=True)
    plt.close(fig1)

    # create plot for red team
    fig2, ax2 = plt.subplots(figsize=(3,3))
    ax2.bar(range(5), values[5:], align='center', color='red')
    ax2.set_title('Damage Dealt to Champions', color='white')
    ax2.set_xticks(range(5))
    # set pictures as labels
    ax2.set_xticklabels([' ', ' ', ' ', ' ', ' '])
    ax2.tick_params(axis='x', which='major', pad=26)
    ax2.set_yticks([])
    for i, c in enumerate(labels[5:]):
        offset_image(i, c, ax2)
    # hide border
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    # add text to bars
    for i, v in enumerate(values[5:]):
        ax2.text(i, v, str(v), ha='center', color='white')
    fig2.tight_layout()
    fig2.savefig(os.path.join('static/images/graphs', f"redTeam{str(parsedMatch['gameId'])}.png"), transparent=True)
    plt.close(fig2)

    return {'id': parsedMatch['gameId'], 'gameType': gameType, 'championIcon': CHAMPION_SQUARE_ICON + championIdMap[parsedMatch['champion']] + '.png', 'kills': kills, 'deaths': deaths, 'assists': assists, 'item0': ITEM_URL + item0, 'item1': ITEM_URL + item1, 'item2': ITEM_URL + item2, 'item3': ITEM_URL + item3, 'item4': ITEM_URL + item4, 'item5': ITEM_URL + item5, 'item6': ITEM_URL + item6, 'damage': damage, 'win': win, 'side': side, 'wardsPlaced': wardsPlaced, 'totalCS': totalCS, 'gameLength': gameLength, 'avgCsPerMin': avgCsPerMin, 'blueTeamKills': blueTeamKills, 'blueTeamWards': blueTeamTotalWardsPlaced, 'redTeamWards': redTeamTotalWardsPlaced, 'blueTeamFirstDragon': blueTeamFirstDragon, 'blueTeamDragonKills': blueTeamDragonKills, 'blueTeamFirstRiftHerald': blueTeamFirstRiftHerald, 'blueTeamRiftHeraldKills': blueTeamRiftHeraldKills, 'blueTeamFirstBaron': blueTeamFirstBaron, 'blueTeamBaronKills': blueTeamBaronKills, 'blueTeamFirstBlood': blueTeamFirstBlood, 'blueTeamFirstTower': blueTeamFirstTower, 'blueTeamTowerKills': blueTeamTowerKills, 'redTeamKills': redTeamKills, 'redTeamFirstDragon': redTeamFirstDragon, 'redTeamDragonKills': redTeamDragonKills, 'redTeamFirstRiftHerald': redTeamFirstRiftHerald, 'redTeamRiftHeraldKills': redTeamRiftHeraldKills, 'redTeamFirstBaron': redTeamFirstBaron, 'redTeamBaronKills': redTeamBaronKills, 'redTeamFirstBlood': redTeamFirstBlood, 'redTeamFirstTower': redTeamFirstTower, 'redTeamTowerKills': redTeamTowerKills, 'players': players}

# make image as label
def offsetImageGlobal(coord, name, ax):
    CHAMPION_SQUARE_ICON = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/champion/'
    img = plt.imread(f"{CHAMPION_SQUARE_ICON}{name}.png")
    im = OffsetImage(img, zoom=0.2)
    im.image.axes = ax

    ab = AnnotationBbox(im, (coord, 0),  xybox=(0., -16.), frameon=False, xycoords='data',  boxcoords="offset points", pad=0)
    ax.add_artist(ab)
