import os
import telebot
from datetime import timedelta, datetime, date 
import pytz
import requests
import json
import csv
import schedule
import time
from threading import Thread
from PIL import Image, ImageFont, ImageDraw

# Get credentials
BOT_TOKEN = ${{ secrets.BOT_TOKEN }}
bot = telebot.TeleBot(BOT_TOKEN)

# Import list of teams and abbreviations
teams = [[24,'Anaheim Ducks', 'ANA','ana','Anaheim','Ducks','anaheim','ducks','anaheim ducks'], [53,'Arizona Coyotes','ARZ','arz''Arizona','Coyotes','Yotes','arizona','coyotes','yotes','arizona coyotes'], [6,'Boston Bruins', 'BOS','bos','Boston','Bruins','boston','bruins','boston bruins'], [7,'Buffalo Sabres', 'BUF','buf','Buffalo','Sabres','buffalo','sabres','buffalo sabres'], [20,'Calgary Flames', 'CGY','cgy','Calgary','Flames','calgary','flames','calgary flames'], [12,'Carolina Hurricanes', 'CAR','car','Carolina','Hurricanes','Canes','carolina','hurricanes','canes','carolina hurricanes'], [16,'Chicago Blackhawks', 'CHI','chi','Chicago','Blackhawks','Hawks','chicago','blackhawks','hawks','chicago blackhawks'], [21,'Colorado Avalanche', 'COL','col','Colorado','Avalanche','Avs','colorado','avalanche','avs','colorado avalanche'], [29,'Columbus Blue Jackets', 'CBJ','cbj','Columbus','Blue Jackets','Jackets','columbus','blue jackets','jackets','columbus blue jackets'], [25,'Dallas Stars', 'DAL','dal','Dallas','Stars','dallas','stars','dallas stars'], [17,'Detroit Red Wings', 'DET','Detroit','Red Wings','Wings','det','detroit','red wings','wings','detroit red wings'], [22,'Edmonton Oilers', 'EDM','Edmonton','Oilers','edm','edmonton','oilers','edmonton oilers'], [13,'Florida Panthers', 'FLA','Florida','Panthers','florida','fla','panthers','florida panthers','Cats','cats'], [26,'Los Angeles Kings', 'LAK','Los Angeles','LA','Kings','lak','la','los angeles','kings','los angeles kings','LA Kings','la kings'], [30,'Minnesota Wild', 'MIN','Minnesota','Wild','min','minnesota','wild','minnesota wild'], [8,'Montréal Canadiens', 'MTL','Montreal','Montréal','Canadiens','Habs','montreal','canadiens','montreal canadiens','Montreal Canadiens'], [18,'Nashville Predators', 'NSH','Nashville','Predators','Preds','nsh','nashville','predators','preds','nashville predators'], [1,'New Jersey Devils', 'NJD','New Jersey','NJ','Devils','nj devils','NJ Devils','new jersey','nj','njd','devils','new jersey devils'], [2,'New York Islanders', 'NYI','NY Islanders','Islanders','Isles','nyi','ny islanders','isles','new york islanders','islanders'], [3,'New York Rangers', 'NYR','NY Rangers','Rangers','Rags','ny rangers','nyr','rangers','new york rangers','rags'], [9,'Ottawa Senators', 'OTT','Ottawa','Senators','Sens','ott','ottawa','senators','sens','ottawa senators'], [4,'Philadelphia Flyers', 'PHL','Philadelphia','Philly','Flyers','philly','phl','flyers','philadelphia','philadelphia flyers'], [5,'Pittsburgh Penguins', 'PIT','Pittsbugh','Penguins','Pens','pit','pittsburgh','penguins','pens','pittsburgh penguins'], [28,'San Jose Sharks', 'SJS','San Jose','SJ','Sharks','sjs','sj','san jose','san jose sharks','sharks'], [55,'Seattle Kraken', 'SEA','Seattle','Kraken','sea','seattle','kraken'], [19,'St. Louis Blues', 'STL','St. Louis','Blues','stl','st. louis blues','st louis','st louis blues','st. louis','blues'], [14,'Tampa Bay Lightning', 'TBL','Tampa Bay','Tampa','TB','Lightning','Bolts','tb','tbl','tampa','tampa bay','lightning','bolts','tampa bay lightning'], [10,'Toronto Maple Leafs', 'TOR','Toronto','Maple Leafs','Leafs','tor','toronto','leafs','maple leafs','toronto maple leafs'], [23,'Vancouver Canucks', 'VAN','Vancouver','Canucks','canucks','vancouver','vancouver canucks','van'], [54,'Vegas Golden Knights', 'VGK','Vegas','Las Vegas','Golden Knights','Knights','vgk','vegas','vegas golden knights','knights','golden knights'], [15,'Washington Capitals', 'WSH','Washington','DC','Capitals','Caps','washington','dc','caps','capitals','washington capitals','wsh'], [52,'Winnipeg Jets', 'WPG','Winnipeg','Jets','winnipeg','wpg','jets','winnipeg jets']]


#### AUXILIARY FUNCTIONS ####
# Define function to schedule daily posts
def daily_games():
	todayRaw = datetime.now()
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)
	url = "https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.broadcasts&date=" + today
	response = requests.get(url)
	data = response.json()

	# Get number of games today. Used for formatting schedule graphic.
	totalGames = data['totalGames']

	if totalGames == 0: # no games today :(
		bot.send_message(-1001961098336, "Today's schedule: \n\nno :(") 
	else:
		# Establish class in which to store games
		class Game:
			def __init__(self, away, home, startTime, TV):
				self.away = away
				self.home = home
				self.startTime = startTime 
				self.TV = TV

		# Create array to store games
		games = []

		# Iteratively add games to array 
		for g in range(0, totalGames):
			awayTeam = data['dates'][0]['games'][g]['teams']['away']['team']['name']
			for t in teams:
				if t[1] == awayTeam:
					awayTeam = t[2]
			homeTeam = data['dates'][0]['games'][g]['teams']['home']['team']['name']
			for t in teams:
				if t[1] == homeTeam:
					homeTeam = t[2]
			puckDrop = data['dates'][0]['games'][g]['gameDate']
			puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
			puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
			puckDrop = puckDrop.strftime('%-I:%M ET')
			broadcast = ""

			# Check to see whether there are broadcasters listed for this game
			h = data['dates'][0]['games'][g]
			if "broadcasts" in h:
				for b in h['broadcasts']:
					# Find only national broadcasters
					if b['type'] == "national":
						broadcast = b['name']
						break

			games.append(Game(awayTeam, homeTeam, puckDrop, broadcast))

		# IMAGE CREATION
		# Get font file
		fontIBM = ImageFont.truetype("IBMPlexSans-Bold.ttf", 50)

		# Create list element to store images in
		gameList = []

		# Iterate through games
		for i in games:
			awayLogo = Image.open("Away Logos/" + i.away + ".png")
			homeLogo = Image.open("Home Logos/" + i.home + ".png")
			base = Image.open("base.png")
			atsign = Image.open("at.png")

			# If the game is on national TV
			if len(i.TV) > 0: 
				TVLogo = Image.open(i.TV + ".png")
				graphic = Image.alpha_composite(base, TVLogo)
				graphic = Image.alpha_composite(graphic, homeLogo)
				graphic = Image.alpha_composite(graphic, awayLogo)
				graphic = Image.alpha_composite(graphic, atsign)

				addText = Image.new("RGBA",(600,300))
				t = ImageDraw.Draw(addText)
				textLocation = 48 + ((len(i.startTime)-7)*14)
				t.text((textLocation,230), i.startTime, fill="#000000", font=fontIBM)
				graphic = Image.alpha_composite(graphic, addText)
			# If the game is NOT nationally televised
			else:
				graphic = Image.alpha_composite(base, homeLogo)
				graphic = Image.alpha_composite(graphic, awayLogo)
				graphic = Image.alpha_composite(graphic, atsign)

				addText = Image.new("RGBA",(600,300))
				t = ImageDraw.Draw(addText)
				textLocation = 212 - ((len(i.startTime)-7)*14)
				t.text((textLocation,230), i.startTime, fill="#000000", font=fontIBM)
				graphic = Image.alpha_composite(graphic, addText)

			# File name to temporarily house graphic is structured as AWAYHOME
			gameName = 'Graphics/' + i.away + i.home + '.png'
			graphic.save(gameName)

			# Graphic is complete. Add file name to list of games
			gameList.append(gameName)


		# This function will combine all of our graphics into one image
		def combine_images(columns, space, images):
		    rows = len(images) // columns
		    if len(images) % columns:
		        rows += 1
		    width_max = max([Image.open(image).width for image in images])
		    height_max = max([Image.open(image).height for image in images])
		    background_width = width_max*columns + (space*columns)-space + (space*2)
		    background_height = height_max*rows + (space*rows)-space + (space*2)
		    background = Image.new('RGBA', (background_width, background_height), (255, 255, 255, 255))
		    x = space
		    y = space
		    for i, image in enumerate(images):
		        img = Image.open(image)
		        x_offset = int((width_max-img.width)/2)
		        y_offset = int((height_max-img.height)/2)
		        background.paste(img, (x+x_offset, y+y_offset))
		        x += width_max + space
		        if (i+1) % columns == 0:
		            y += height_max + space
		            x = space
		    background.save('games-today.png')
		    bot.send_photo(-1001961098336, photo=open('games-today.png','rb'))

		# Use number of games from earlier to establish width of grid
		if totalGames == 1: 
			numColumns = 1
		elif totalGames in [2,4]:
			numColumns = 2
		elif totalGames in [3,5,6,9,11,14,15]:
			numColumns = 3
		elif totalGames in [7,8,12,16]:
			numColumns = 4
		else: # just 10 and 13
			numColumns = 5

		combine_images(columns=numColumns, space=10, images=gameList)


# Define function to get games
def get_games(message, gameday):
	url = "https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.broadcasts&date=" + gameday
	response = requests.get(url)
	data = response.json()

	# Get number of games today. Used for formatting schedule graphic.
	totalGames = data['totalGames']

	if totalGames == 0: # no games today :(
		bot.send_message(message.chat.id, "No games found for this date :(") 
	else:
		# Establish class in which to store games
		class Game:
			def __init__(self, away, home, startTime, TV):
				self.away = away
				self.home = home
				self.startTime = startTime 
				self.TV = TV

		# Create array to store games
		games = []

		# Iteratively add games to array 
		for g in range(0, totalGames):
			awayTeam = data['dates'][0]['games'][g]['teams']['away']['team']['name']
			for t in teams:
				if t[1] == awayTeam:
					awayTeam = t[2]
			homeTeam = data['dates'][0]['games'][g]['teams']['home']['team']['name']
			for t in teams:
				if t[1] == homeTeam:
					homeTeam = t[2]
			puckDrop = data['dates'][0]['games'][g]['gameDate']
			puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
			puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
			puckDrop = puckDrop.strftime('%-I:%M ET')
			broadcast = ""

			# Check to see whether there are broadcasters listed for this game
			h = data['dates'][0]['games'][g]
			if "broadcasts" in h:
				for b in h['broadcasts']:
					# Find only national broadcasters
					if b['type'] == "national":
						broadcast = b['name']
						break

			games.append(Game(awayTeam, homeTeam, puckDrop, broadcast))

		# IMAGE CREATION
		# Get font file
		fontIBM = ImageFont.truetype("IBMPlexSans-Bold.ttf", 50)

		# Create list element to store images in
		gameList = []

		# Iterate through games
		for i in games:
			awayLogo = Image.open("Away Logos/" + i.away + ".png")
			homeLogo = Image.open("Home Logos/" + i.home + ".png")
			base = Image.open("base.png")
			atsign = Image.open("at.png")

			# If the game is on national TV
			if len(i.TV) > 0: 
				TVLogo = Image.open(i.TV + ".png")
				graphic = Image.alpha_composite(base, TVLogo)
				graphic = Image.alpha_composite(graphic, homeLogo)
				graphic = Image.alpha_composite(graphic, awayLogo)
				graphic = Image.alpha_composite(graphic, atsign)

				addText = Image.new("RGBA",(600,300))
				t = ImageDraw.Draw(addText)
				textLocation = 48 + ((len(i.startTime)-7)*14)
				t.text((textLocation,230), i.startTime, fill="#000000", font=fontIBM)
				graphic = Image.alpha_composite(graphic, addText)
			# If the game is NOT nationally televised
			else:
				graphic = Image.alpha_composite(base, homeLogo)
				graphic = Image.alpha_composite(graphic, awayLogo)
				graphic = Image.alpha_composite(graphic, atsign)

				addText = Image.new("RGBA",(600,300))
				t = ImageDraw.Draw(addText)
				textLocation = 212 - ((len(i.startTime)-7)*14)
				t.text((textLocation,230), i.startTime, fill="#000000", font=fontIBM)
				graphic = Image.alpha_composite(graphic, addText)

			# File name to temporarily house graphic is structured as AWAYHOME
			gameName = 'Graphics/' + i.away + i.home + '.png'
			graphic.save(gameName)

			# Graphic is complete. Add file name to list of games
			gameList.append(gameName)


		# This function will combine all of our graphics into one image
		def combine_images(columns, space, images):
		    rows = len(images) // columns
		    if len(images) % columns:
		        rows += 1
		    width_max = max([Image.open(image).width for image in images])
		    height_max = max([Image.open(image).height for image in images])
		    background_width = width_max*columns + (space*columns)-space + (space*2)
		    background_height = height_max*rows + (space*rows)-space + (space*2)
		    background = Image.new('RGBA', (background_width, background_height), (255, 255, 255, 255))
		    x = space
		    y = space
		    for i, image in enumerate(images):
		        img = Image.open(image)
		        x_offset = int((width_max-img.width)/2)
		        y_offset = int((height_max-img.height)/2)
		        background.paste(img, (x+x_offset, y+y_offset))
		        x += width_max + space
		        if (i+1) % columns == 0:
		            y += height_max + space
		            x = space
		    background.save('games-today.png')
		    bot.send_photo(message.chat.id, photo=open('games-today.png','rb'))

		# Use number of games from earlier to establish width of grid
		if totalGames == 1: 
			numColumns = 1
		elif totalGames in [2,4]:
			numColumns = 2
		elif totalGames in [3,5,6,9,11,14,15]:
			numColumns = 3
		elif totalGames in [7,8,12,16]:
			numColumns = 4
		else: # just 10 and 13
			numColumns = 5

		combine_images(columns=numColumns, space=10, images=gameList)

# Verify that a selected date exists and is valid
def date_validation(message, dateInput):
	if dateInput[:9] == '/schedule':
		dateInput = dateInput[10:]
	isValid = 1
	try:
		dateElement = date.fromisoformat(dateInput)
	except ValueError:
		isValid = 0
		text = "Date must be formatted as YYYY-MM-DD. Re-enter the /schedule command to retry."

	if isValid == 1:
		if not date(2023,7,1) <= dateElement <= date(2024,6,30):
			isValid = 0
			text = "Date must be between 2023-07-01 and 2024-06-30. Re-enter the /schedule command to retry."
	
	if isValid == 0:
		bot.send_message(message.chat.id, text)
	else:
		dateString = str(dateElement)
		get_games(message, dateString)

# Define function for selecting a date
def day_handler(message):
	dateInput = message.text
	date_validation(message, dateInput)

# Verify that a selected team exists and if so, send their next game
def team_validation(message, teamInput):
	if teamInput[:9] == '/nextgame':
		teamInput = teamInput[10:]
	teamId = 0
	for e in teams:
		if teamInput in e:
			teamId = e[0]
			teamName = e[1]

	if teamId == 0:
		# team does not exist or is misspelled
		bot.reply_to(message, "Hmm, I don't know that team. Re-enter the /nextgame command to retry.")
	else: 
		# this team exists! let's figure out their next game
		todayRaw = datetime.now() # start with today
		endRaw = todayRaw + timedelta(days=14) # search next two weeks
		startDate = todayRaw.strftime('%Y-%m-%d')
		endDate = endRaw.strftime('%Y-%m-%d')
		startDate = str(startDate)
		endDate = str(endDate)

		# much of this is lifted from get_games function
		url = "https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.broadcasts&teamId=" + str(teamId) + "&startDate=" + startDate + "&endDate=" + endDate
		response = requests.get(url)
		data = response.json()

		totalGames = data['totalGames']

		if totalGames == 0: # no games over the next two weeks :(
			bot.reply_to(message, "Sorry fam. I don't see any games on the schedule for this team over the next couple weeks.") 
		else:
			firstGameState = data['dates'][0]['games'][0]['status']['codedGameState']
			if firstGameState == "1": # this is the next game
				awayTeam = data['dates'][0]['games'][0]['teams']['away']['team']['name']
				homeTeam = data['dates'][0]['games'][0]['teams']['home']['team']['name']
				puckDrop = data['dates'][0]['games'][0]['gameDate']
				puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
				puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
				puckDrop2 = puckDrop.strftime('%B %d')
				puckDrop = puckDrop.strftime('%-I:%M ET')
				broadcast = ""

				# Check to see whether there are broadcasters listed for this game
				h = data['dates'][0]['games'][0]
				if "broadcasts" in h:
					for b in h['broadcasts']:
						# Find only national broadcasters
						if b['type'] == "national":
							broadcast = " on " + b['name']
							break

				if data['dates'][0]['date'] == startDate: # game is today
					answer = "The " + teamName + " play today! \n"
				else: # game is some other day
					answer = "The " + teamName + " play their next game on " + puckDrop2 + ": \n\n"

				answer = answer + awayTeam + " at " + homeTeam + ", " + puckDrop + broadcast
				bot.reply_to(message, answer) 


			else: # whoops, today's game was already played. let's grab the next one
				if totalGames > 0: # gotta make sure there IS another game coming up
					awayTeam = data['dates'][1]['games'][0]['teams']['away']['team']['name']
					for t in teams:
						if t[1] == awayTeam:
							awayTeam = t[2]
					homeTeam = data['dates'][1]['games'][0]['teams']['home']['team']['name']
					for t in teams:
						if t[1] == homeTeam:
							homeTeam = t[2]
					puckDrop = data['dates'][1]['games'][0]['gameDate']
					puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
					puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
					puckDrop2 = puckDrop.strftime('%B %-d')
					puckDrop = puckDrop.strftime('%-I:%M ET')
					broadcast = ""

					# Check to see whether there are broadcasters listed for this game
					h = data['dates'][1]['games'][0]
					if "broadcasts" in h:
						for b in h['broadcasts']:
							# Find only national broadcasters
							if b['type'] == "national":
								broadcast = b['name']
								break

					answer = "The " + teamName + " play their next game on " + puckDrop2 + ". \n"
					answer = answer + awayTeam + " at " + homeTeam + ", " + puckDrop + broadcast
					bot.reply_to(message, answer) 
				else:
					bot.reply_to(message, "Sorry fam. I don't see any games on the schedule for this team over the next couple weeks.")  

def teams_validation(message, teamsInput):
	teamId1 = 0
	teamId2 = 0
	team1 = teamsInput[0:3]
	team2 = teamsInput[4:7]

	for e in teams:
		if team1 in e:
			teamId1 = e[0]
			teamName1 = e[1]
		if team2 in e:
			teamId2 = e[0]
			teamName2 = e[1]

	if teamId1 == 0 or teamId2 == 0:
		# team does not exist or is misspelled
		bot.reply_to(message, "Hmm, I don't know at least one of those team. Re-enter the /nextmatchup command to retry.")
	else: 
		todayRaw = datetime.now() # start with tomorrow
		todayRaw = todayRaw + timedelta(days=1) # make it tomorrow
		startDate = todayRaw.strftime('%Y-%m-%d')
		startDate = str(startDate)

		# this will grab all games for Team 1 for the rest of the season
		url = "https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.broadcasts&teamId=" + str(teamId1) + "&startDate=" + startDate + "&endDate=2024-06-30"
		response = requests.get(url)
		data = response.json()

		totalGames = data['totalGames']

		if totalGames == 0: # no games the rest of the season :(
			bot.reply_to(message, "Oops, looks like their regular season's already over.") 
		else:
			matchFound = 0
			for g in range(0,totalGames):
				away = data['dates'][g]['games'][0]['teams']['away']['team']['id']
				home = data['dates'][g]['games'][0]['teams']['home']['team']['id']
				if away == teamId2 or home == teamId2:
					awayName = data['dates'][g]['games'][0]['teams']['away']['team']['name']
					homeName = data['dates'][g]['games'][0]['teams']['home']['team']['name']
					puckDrop = data['dates'][g]['games'][0]['gameDate']
					puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
					puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
					puckDrop2 = puckDrop.strftime('%B %-d')
					puckDrop = puckDrop.strftime('%-I:%M ET')
					matchFound = 1
					break
			if matchFound == 0:
				bot.reply_to(message, "Sorry, doesn't look like these teams play again in the regular season.")
			else:
				bot.reply_to(message, "Here's the next matchup for these teams: \n\n" + awayName + " at " + homeName + " on " + puckDrop2)
				

# Define function for selecting a team
def team_handler(message):
	teamInput = message.text
	team_validation(message, teamInput)

# Define function for selecting multiple teams
def teams_handler(message):
	teamsInput = message.text
	teams_validation(message, teamsInput)

#### USER INTERACTIONS
# Example interaction
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Beep boop, I'm the NHL schedule bot. I will never know the touch of another person. I will never see the sunrise on a brisk autumn morning, or gaze up at the stars in a field far from civilization. But I know the NHL schedule like the back of my hand — which, again, I do not actually possess. How can I help you?\n \n /today: Get today's schedule \n /tomorrow: Get tomorrow's schedule \n /schedule: Get the schedule for a specific date. Accepts date parameter in YYYY-MM-DD format \n /nextgame: Get the next game for a specific team. Accepts team parameter (city, abbreviation, nickname, etc.) \n /nextmatchup: Get the next matchup between two specified teams. Requires the three-letter abbreviations of two teams (e.g. /nextmatchup LAK PHL)")

# Get today's games
@bot.message_handler(commands=['today'])
def games_today(message):
	todayRaw = datetime.now()
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)
	get_games(message, today)

# Get tomorrow's games
@bot.message_handler(commands=['tomorrow'])
def games_tomorrow(message):
	todayRaw = datetime.now()
	todayRaw = todayRaw + timedelta(days=1)
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)
	get_games(message, today)

# Get games for a user-provided date
@bot.message_handler(commands=['schedule'])
def games_on_date(message):
	if len(message.text) > 18:
		dateArg = message.text[10:]
		date_validation(message, dateArg)
	else:
		text = "Enter a date in YYYY-MM-DD format:"
		sent_msg = bot.reply_to(message, text)
		bot.register_next_step_handler(sent_msg, day_handler)

# Get the next game for a specific team
@bot.message_handler(commands=['nextgame'])
def next_game(message):
	if len(message.text) > 11:
		teamArg = message.text[10:]
		team_validation(message, teamArg)
	else:
		text = "Which team?"
		sent_msg = bot.reply_to(message, text)
		bot.register_next_step_handler(sent_msg, team_handler)

# Get the next matchup between two specific teams
@bot.message_handler(commands=['nextmatchup'])
def next_game(message):
	if len(message.text) == 20:
		teamsArg = message.text[13:]
		teams_validation(message, teamsArg)
	else:
		text = "Send the three-letter abbreviations of the two teams you're interested in. (Note: All abbreviations match those used on NHL.com except Arizona (ARZ) and Philadelphia (PHL), because mine are better.)"
		sent_msg = bot.reply_to(message, text)
		bot.register_next_step_handler(sent_msg, teams_handler)


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.send_message(message.chat.id, "Enter commands with a slash followed by the command. Possible commands: \n \n⏵ /today: Get today's schedule \n⏵ /tomorrow: Get tomorrow's schedule \n⏵ /schedule: Get the schedule for a specific date. Accepts date parameter in YYYY-MM-DD format \n⏵ /nextgame: Get the next game for a specific team. Accepts team parameter (city, abbreviation, nickname, etc.) \n⏵ /nextmatchup: Get the next matchup between two specified teams. Requires the three-letter abbreviations of two teams (e.g. /nextmatchup LAK PHL)")


def schedule_checker():
	while True:
		schedule.run_pending()
		time.sleep(1)

# this will run once per day starting at 9 a.m. If launched after 9 a.m., it will run immediately
schedule.every().day.at("09:00","US/Eastern").do(daily_games) 
Thread(target=schedule_checker).start()

bot.infinity_polling()
