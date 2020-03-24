from flask import Flask, render_template, redirect, url_for, request
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/profile', methods=['POST'])
def profile():
    return redirect(url_for('showProfile', name=request.form['summonerName']))
    
@app.route('/profile/<name>')
def showProfile(name):

    # variables declared locally for performance improvement
    import requests, json, os
    from markupsafe import escape
    from exports import championIdMap, queueTypes, itemMap
    API = f"?api_key={os.getenv('API_KEY')}"
    SUMMONER_URL = 'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/'
    PROFILE_ICON = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/profileicon/'
    RANKED_URL = 'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/'
    MASTERY_URL = 'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/'
    MATCHLIST_URL = 'https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/'
    CHAMPION_SQUARE_ICON = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/champion/'
    CHAMPION_LOADING_ICON = 'http://ddragon.leagueoflegends.com/cdn/img/champion/loading/'
    MATCH_URL = 'https://na1.api.riotgames.com/lol/match/v4/matches/'
    ITEM_URL = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/item/'
    
    # get summoner info
    res = requests.get(f"{SUMMONER_URL}{escape(name)}{API}")
    summonerData = json.loads(res.text)
    
    imgLink = f"{PROFILE_ICON}{str(summonerData['profileIconId'])}.png"
    summonerLevel = summonerData['summonerLevel']
    
    # get ranked info
    res = requests.get(f"{RANKED_URL}{str(summonerData['id'])}{API}")
    parsedRankedData = json.loads(res.text)
    
    rankedData = {'rank': '', 'numWins': 0, 'numLosses': 0, 'queueType': ''}
    if parsedRankedData:
        rankedData['rank'] = f"{parsedRankedData[0]['tier']} {parsedRankedData[0]['rank']}"
        rankedData['numWins'] = parsedRankedData[0]['wins']
        rankedData['numLosses'] = parsedRankedData[0]['losses']
        rankedData['queueType'] = parsedRankedData[0]['queueType']

    # get champion mastery info
    res = requests.get(f"{MASTERY_URL}{str(summonerData['id'])}{API}")
    parsedMasteryData = json.loads(res.text)
    
    parsedMasteryData = parsedMasteryData[:3]
    masteryData = []
    for champion in parsedMasteryData:
        mastery = {'championIcon': f"{CHAMPION_LOADING_ICON}{championIdMap[champion['championId']]}_0.jpg", 'championName': championIdMap[champion['championId']], 'level': champion['championLevel'], 'points': champion['championPoints']}
        masteryData.append(mastery)

    # get match history
    res = requests.get(f"{MATCHLIST_URL}{str(summonerData['accountId'])}{API}")
    parsedMatchList = json.loads(res.text)
    parsedMatchList = parsedMatchList['matches'][:10]

    # get individual game info
    matchList = []
    for parsedMatch in parsedMatchList:
        res = requests.get(f"{MATCH_URL}{str(parsedMatch['gameId'])}{API}")
        matchData = json.loads(res.text)
        
        # get type of game (e.g. ranked, normal, custom)
        gameType = ''
        queueId = parsedMatch['queue']
        for queueType in queueTypes:
            if queueId == queueType['queueId']:
                if queueType['queueId'] == 0:
                    gameType = 'Custom'
                else:
                    gameType = queueType['description'][:-6]
        
        # get participant id and all participant names and ids
        participants = {} # key: participant ID, value: dict = {keys: name, kills, deaths, assists}
        participantId = -1
        for participant in matchData['participantIdentities']:
            participants[participant['participantId']] = {'summonerName': participant['player']['summonerName']}
            if participant['player']['summonerId'] == summonerData['id']:
                participantId = participant['participantId']
                
        # use participant id to find player stats
        kills = 0
        deaths = 0
        assists = 0
        damage = 0
        win = True
        wardsPlaced = 0
        side = 'Blue'
        avgCsPerMin = 0
        totalCS = 0
        gameLength = 0
        item0 = ''
        item1 = ''
        item2 = ''
        item3 = ''
        item4 = ''
        item5 = ''
        item6 = ''
        
        # blue and red team info
        blueTeamKills = 0
        blueTeamFirstDragon = matchData['teams'][0]['firstDragon']
        blueTeamDragonKills = matchData['teams'][0]['dragonKills']
        blueTeamFirstRiftHerald = matchData['teams'][0]['firstRiftHerald']
        blueTeamRiftHeraldKills = matchData['teams'][0]['riftHeraldKills']
        blueTeamFirstBaron = matchData['teams'][0]['firstBaron']
        blueTeamBaronKills = matchData['teams'][0]['baronKills']
        blueTeamFirstBlood = matchData['teams'][0]['firstBlood']
        blueTeamFirstTower = matchData['teams'][0]['firstTower']
        blueTeamTowerKills = matchData['teams'][0]['towerKills']
        blueTeamTotalWardsPlaced = 0 # teamId = 100
        redTeamKills = 0
        redTeamFirstDragon = matchData['teams'][1]['firstDragon']
        redTeamDragonKills = matchData['teams'][1]['dragonKills']
        redTeamFirstRiftHerald = matchData['teams'][1]['firstRiftHerald']
        redTeamRiftHeraldKills = matchData['teams'][1]['riftHeraldKills']
        redTeamFirstBaron = matchData['teams'][1]['firstBaron']
        redTeamBaronKills = matchData['teams'][1]['baronKills']
        redTeamFirstBlood = matchData['teams'][1]['firstBlood']
        redTeamFirstTower = matchData['teams'][1]['firstTower']
        redTeamTowerKills = matchData['teams'][1]['towerKills']
        redTeamTotalWardsPlaced = 0 # teamId = 200
        
        # for plotting damage dealt
        labels = []
        values = []
        
        for participant in matchData['participants']:
        
            # get all participant's champion, kda, damage, cs
            participants[participant['participantId']]['champion'] = championIdMap[participant['championId']]
            participants[participant['participantId']]['kills'] = participant['stats']['kills']
            participants[participant['participantId']]['deaths'] = participant['stats']['deaths']
            participants[participant['participantId']]['assists'] = participant['stats']['assists']
            participants[participant['participantId']]['cs'] = participant['stats']['totalMinionsKilled'] + participant['stats']['neutralMinionsKilled']
        
            teamId = participant['teamId']
            
            if teamId == 100:
                blueTeamKills += participant['stats']['kills']
                blueTeamTotalWardsPlaced += participant['stats']['wardsPlaced']
            else:
                redTeamKills += participant['stats']['kills']
                redTeamTotalWardsPlaced += participant['stats']['wardsPlaced']
                
            if participant['participantId'] == participantId:
                kills = participant['stats']['kills']
                deaths = participant['stats']['deaths']
                assists = participant['stats']['assists']
                damage = participant['stats']['totalDamageDealtToChampions']
                win = participant['stats']['win']
                wardsPlaced = participant['stats']['wardsPlaced']
                avgCsPerMin = int((participant['stats']['totalMinionsKilled'] + participant['stats']['neutralMinionsKilled']) // (matchData['gameDuration'] / 60))
                totalCS = participant['stats']['totalMinionsKilled'] + participant['stats']['neutralMinionsKilled']
                minutes = matchData['gameDuration'] // 60
                seconds = matchData['gameDuration'] - (minutes * 60)
                if seconds < 10:
                    gameLength = str(minutes) + ':0' + str(seconds)
                else:
                    gameLength = str(minutes) + ':' + str(seconds)
                if participant['stats']['item0'] != 0:
                    item0 = itemMap['data'][str(participant['stats']['item0'])]['image']['full']
                if participant['stats']['item1'] != 0:
                    item1 = itemMap['data'][str(participant['stats']['item1'])]['image']['full']
                if participant['stats']['item2'] != 0:
                    item2 = itemMap['data'][str(participant['stats']['item2'])]['image']['full']
                if participant['stats']['item3'] != 0:
                    item3 = itemMap['data'][str(participant['stats']['item3'])]['image']['full']
                if participant['stats']['item4'] != 0:
                    item4 = itemMap['data'][str(participant['stats']['item4'])]['image']['full']
                if participant['stats']['item5'] != 0:
                    item5 = itemMap['data'][str(participant['stats']['item5'])]['image']['full']
                if participant['stats']['item6'] != 0:
                    item6 = itemMap['data'][str(participant['stats']['item6'])]['image']['full']
                if teamId == 200:
                    side = 'Red'
                    
            labels.append(championIdMap[participant['championId']])
            values.append(participant['stats']['totalDamageDealtToChampions'])
        
        # create plot for blue team
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
        
        match = {'id': parsedMatch['gameId'], 'gameType': gameType, 'championIcon': CHAMPION_SQUARE_ICON + championIdMap[parsedMatch['champion']] + '.png', 'kills': kills, 'deaths': deaths, 'assists': assists, 'item0': ITEM_URL + item0, 'item1': ITEM_URL + item1, 'item2': ITEM_URL + item2, 'item3': ITEM_URL + item3, 'item4': ITEM_URL + item4, 'item5': ITEM_URL + item5, 'item6': ITEM_URL + item6, 'damage': damage, 'win': win, 'side': side, 'wardsPlaced': wardsPlaced, 'totalCS': totalCS, 'gameLength': gameLength, 'avgCsPerMin': avgCsPerMin, 'blueTeamKills': blueTeamKills, 'blueTeamWards': blueTeamTotalWardsPlaced, 'redTeamWards': redTeamTotalWardsPlaced, 'blueTeamFirstDragon': blueTeamFirstDragon, 'blueTeamDragonKills': blueTeamDragonKills, 'blueTeamFirstRiftHerald': blueTeamFirstRiftHerald, 'blueTeamRiftHeraldKills': blueTeamRiftHeraldKills, 'blueTeamFirstBaron': blueTeamFirstBaron, 'blueTeamBaronKills': blueTeamBaronKills, 'blueTeamFirstBlood': blueTeamFirstBlood, 'blueTeamFirstTower': blueTeamFirstTower, 'blueTeamTowerKills': blueTeamTowerKills, 'redTeamKills': redTeamKills, 'redTeamFirstDragon': redTeamFirstDragon, 'redTeamDragonKills': redTeamDragonKills, 'redTeamFirstRiftHerald': redTeamFirstRiftHerald, 'redTeamRiftHeraldKills': redTeamRiftHeraldKills, 'redTeamFirstBaron': redTeamFirstBaron, 'redTeamBaronKills': redTeamBaronKills, 'redTeamFirstBlood': redTeamFirstBlood, 'redTeamFirstTower': redTeamFirstTower, 'redTeamTowerKills': redTeamTowerKills, 'participants': participants}
        matchList.append(match)
    
    return render_template('profile.html', summonerName=summonerData['name'], imgLink=imgLink, summonerLevel=summonerLevel, rankedData=rankedData, masteryData=masteryData, matchList=matchList)
    
# make image as label
def offset_image(coord, name, ax):
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    CHAMPION_SQUARE_ICON = 'http://ddragon.leagueoflegends.com/cdn/10.6.1/img/champion/'
    img = plt.imread(f"{CHAMPION_SQUARE_ICON}{name}.png")
    im = OffsetImage(img, zoom=0.2)
    im.image.axes = ax
    
    ab = AnnotationBbox(im, (coord, 0),  xybox=(0., -16.), frameon=False, xycoords='data',  boxcoords="offset points", pad=0)
    ax.add_artist(ab)
    