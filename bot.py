#### GATHER THE INGREDIENTS ####
import os
import telebot
from telebot import types
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
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Import list of teams, IDs and abbreviations
teams = [[24,'Anaheim Ducks', 'ANA','ana','Anaheim','Ducks','anaheim','ducks','anaheim ducks'], [53,'Arizona Coyotes','ARI','arz''Arizona','Coyotes','Yotes','arizona','coyotes','yotes','arizona coyotes'], [6,'Boston Bruins', 'BOS','bos','Boston','Bruins','boston','bruins','boston bruins'], [7,'Buffalo Sabres', 'BUF','buf','Buffalo','Sabres','buffalo','sabres','buffalo sabres'], [20,'Calgary Flames', 'CGY','cgy','Calgary','Flames','calgary','flames','calgary flames'], [12,'Carolina Hurricanes', 'CAR','car','Carolina','Hurricanes','Canes','carolina','hurricanes','canes','carolina hurricanes'], [16,'Chicago Blackhawks', 'CHI','chi','Chicago','Blackhawks','Hawks','chicago','blackhawks','hawks','chicago blackhawks'], [21,'Colorado Avalanche', 'COL','col','Colorado','Avalanche','Avs','colorado','avalanche','avs','colorado avalanche'], [29,'Columbus Blue Jackets', 'CBJ','cbj','Columbus','Blue Jackets','Jackets','columbus','blue jackets','jackets','columbus blue jackets'], [25,'Dallas Stars', 'DAL','dal','Dallas','Stars','dallas','stars','dallas stars'], [17,'Detroit Red Wings', 'DET','Detroit','Red Wings','Wings','det','detroit','red wings','wings','detroit red wings'], [22,'Edmonton Oilers', 'EDM','Edmonton','Oilers','edm','edmonton','oilers','edmonton oilers'], [13,'Florida Panthers', 'FLA','Florida','Panthers','florida','fla','panthers','florida panthers','Cats','cats'], [26,'Los Angeles Kings', 'LAK','Los Angeles','LA','Kings','lak','la','los angeles','kings','los angeles kings','LA Kings','la kings'], [30,'Minnesota Wild', 'MIN','Minnesota','Wild','min','minnesota','wild','minnesota wild'], [8,'Montréal Canadiens', 'MTL','Montreal','Montréal','Canadiens','Habs','montreal','canadiens','montreal canadiens','Montreal Canadiens','habs'], [18,'Nashville Predators', 'NSH','Nashville','Predators','Preds','nsh','nashville','predators','preds','nashville predators'], [1,'New Jersey Devils', 'NJD','New Jersey','NJ','Devils','nj devils','NJ Devils','new jersey','nj','njd','devils','new jersey devils'], [2,'New York Islanders', 'NYI','NY Islanders','Islanders','Isles','nyi','ny islanders','isles','new york islanders','islanders'], [3,'New York Rangers', 'NYR','NY Rangers','Rangers','Rags','ny rangers','nyr','rangers','new york rangers','rags'], [9,'Ottawa Senators', 'OTT','Ottawa','Senators','Sens','ott','ottawa','senators','sens','ottawa senators'], [4,'Philadelphia Flyers', 'PHI','Philadelphia','Philly','Flyers','philly','phl','flyers','philadelphia','philadelphia flyers'], [5,'Pittsburgh Penguins', 'PIT','Pittsbugh','Penguins','Pens','pit','pittsburgh','penguins','pens','pittsburgh penguins'], [28,'San Jose Sharks', 'SJS','San Jose','SJ','Sharks','sjs','sj','san jose','san jose sharks','sharks'], [55,'Seattle Kraken', 'SEA','Seattle','Kraken','sea','seattle','kraken'], [19,'St. Louis Blues', 'STL','St. Louis','Blues','stl','st. louis blues','st louis','st louis blues','st. louis','blues'], [14,'Tampa Bay Lightning', 'TBL','Tampa Bay','Tampa','TB','Lightning','Bolts','tb','tbl','tampa','tampa bay','lightning','bolts','tampa bay lightning'], [10,'Toronto Maple Leafs', 'TOR','Toronto','Maple Leafs','Leafs','tor','toronto','leafs','maple leafs','toronto maple leafs'], [23,'Vancouver Canucks', 'VAN','Vancouver','Canucks','canucks','vancouver','vancouver canucks','van'], [54,'Vegas Golden Knights', 'VGK','Vegas','Las Vegas','Golden Knights','Knights','vgk','vegas','vegas golden knights','knights','golden knights'], [15,'Washington Capitals', 'WSH','Washington','DC','Capitals','Caps','washington','dc','caps','capitals','washington capitals','wsh'], [52,'Winnipeg Jets', 'WPG','Winnipeg','Jets','winnipeg','wpg','jets','winnipeg jets']]


#### AUXILIARY FUNCTIONS ####
# Define function to schedule daily posts
def daily_games():
	# Get current datetime and convert to string format to append to API URL
	todayRaw = datetime.now()
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)
	# Call API and get today's schedule
	url = "https://api-web.nhle.com/v1/schedule/" + today
	response = requests.get(url)
	data = response.json()

	# Get number of games today. Used for formatting schedule graphic.
	totalGames = data['gameWeek'][0]['numberOfGames']

	if totalGames == 0: # no games today :(
		bot.send_message(-1001048436208, "Today's schedule: \n\nno :(") 
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
			awayTeam = data['gameWeek'][0]['games'][g]['awayTeam']['abbrev']
			homeTeam = data['gameWeek'][0]['games'][g]['homeTeam']['abbrev']
			puckDrop = data['gameWeek'][0]['games'][g]['startTimeUTC']
			puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
			puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
			puckDrop = puckDrop.strftime('%-I:%M ET')
			broadcast = ""

			# Check to see whether there are broadcasters listed for this game
			h = data['gameWeek'][0]['games'][g]
			for b in h['tvBroadcasts']:
					# Find only national broadcasters
					if b['market'] == "N" and b['countryCode'] == "US":
						broadcast = b['network']
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
		    # This line sends the schedule graphic to the group chat and saves the message for pinning
		    sentPhoto = bot.send_photo(-1001048436208, photo=open('games-today.png','rb'))
		    # Now let's automatically pin the photo
		    bot.pin_chat_message(-1001048436208, sentPhoto.message_id, True)

		    # bot.send_photo(-1001961098336, photo=open('games-today.png','rb'))


		# Use number of games from earlier to establish width of grid
		# Goal is to have even lines, and no more than 2 empty spaces
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
	# Call NHL API to get schedule for selected day
	url = "https://api-web.nhle.com/v1/schedule/" + gameday
	response = requests.get(url)
	data = response.json()

	# Get number of games today. Used for formatting schedule graphic.
	totalGames = data['gameWeek'][0]['numberOfGames']

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
			awayTeam = data['gameWeek'][0]['games'][g]['awayTeam']['abbrev']
			homeTeam = data['gameWeek'][0]['games'][g]['homeTeam']['abbrev']
			puckDrop = data['gameWeek'][0]['games'][g]['startTimeUTC']
			puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
			puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
			puckDrop = puckDrop.strftime('%-I:%M ET')
			broadcast = ""

			# Check to see whether there are broadcasters listed for this game
			h = data['gameWeek'][0]['games'][g]
			for b in h['tvBroadcasts']:
					# Find only national broadcasters
					if b['market'] == "N" and b['countryCode'] == "US":
						broadcast = b['network']
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
		dateInput = dateInput[10:] # this shaves the command itself from the string passed in
	isValid = 1
	try:
		dateElement = date.fromisoformat(dateInput) 
	except ValueError: # we're checking here to make sure user-submitted dates are formatted properly
		isValid = 0
		text = "Date must be formatted as YYYY-MM-DD. Re-enter the /schedule command to retry."

	if isValid == 1: # if this is 1, then the date has been formatted properly
		if not date(2023,7,1) <= dateElement <= date(2024,6,30): # we want the date to be for this season only
			isValid = 0
			text = "Date must be between 2023-07-01 and 2024-06-30. Re-enter the /schedule command to retry."
	
	# if this is 0, then there's an error somewhere and the user is notified. otherwise we proceed
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
	teamInput = teamInput.lower()
	teamId = "0"
	for e in teams:
		if teamInput in e:
			teamId = e[2]
			teamName = e[1]

	if teamId == "0":
		# team does not exist or is misspelled
		bot.reply_to(message, "Hmm, I don't know that team. Re-enter the /nextgame command to retry.")
	else: 
		# this team exists! let's figure out their next game
		todayRaw = datetime.now() # start with today
		startDate = todayRaw.strftime('%Y-%m-%d')
		startDate = str(startDate)

		# much of this is lifted from get_games function
		url = "https://api-web.nhle.com/v1/club-schedule/" + teamId + "/week/" + startDate
		response = requests.get(url)
		data = response.json()

		totalGames = len(data['games'])

		if totalGames == 0: # no games over the next two weeks :(
			bot.reply_to(message, "Sorry fam. I don't see any games on the schedule for this team over the next week.") 
		else:
			firstGameState = data['games'][0]['gameState']
			if firstGameState == "FUT": # this is the next game
				awayTeam = data['games'][0]['awayTeam']['abbrev']
				homeTeam = data['games'][0]['homeTeam']['abbrev']
				puckDrop = data['games'][0]['startTimeUTC']
				puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
				puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
				puckDrop2 = puckDrop.strftime('%B %d')
				puckDrop = puckDrop.strftime('%-I:%M ET')
				broadcast = ""

				# Check to see whether there are broadcasters listed for this game
				h = data['games'][0]
				for b in h['tvBroadcasts']:
					# Find only national broadcasters
					if b['market'] == "N" and b['countryCode'] == "US":
						broadcast = b['network']
						break

				if data['games'][0]['gameDate'] == startDate: # game is today
					answer = "The " + teamName + " play today! \n"
				else: # game is some other day
					answer = "The " + teamName + " play their next game on " + puckDrop2 + ": \n\n"

				answer = answer + awayTeam + " at " + homeTeam + ", " + puckDrop + " " + broadcast
				bot.reply_to(message, answer)


			else: # whoops, today's game was already played. let's grab the next one
				if totalGames > 1: # gotta make sure there IS another game coming up
					awayTeam = data['games'][1]['awayTeam']['abbrev']
					homeTeam = data['games'][1]['homeTeam']['abbrev']
					puckDrop = data['games'][1]['startTimeUTC']
					puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
					puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
					puckDrop2 = puckDrop.strftime('%B %d')
					puckDrop = puckDrop.strftime('%-I:%M ET')
					broadcast = ""

					# Check to see whether there are broadcasters listed for this game
					h = data['games'][1]
					for b in h['tvBroadcasts']:
						# Find only national broadcasters
						if b['market'] == "N" and b['countryCode'] == "US":
							broadcast = b['network']
							break

					answer = "The " + teamName + " play their next game on " + puckDrop2 + ": \n\n"
					answer = answer + awayTeam + " at " + homeTeam + ", " + puckDrop + " " + broadcast
					bot.reply_to(message, answer) 
				else:
					bot.reply_to(message, "Sorry fam. I don't see any games on the schedule for this team over the next week.")  

def teams_validation(message, teamsInput):
	# this is for the /series command
	# we only accept three-letter abbreviations so I don't have to figure out all the edge cases
	# this next section grabs those three-letter strings and matches them to the proper teams
	team1 = teamsInput[0:3] 
	team2 = teamsInput[4:7]
	team1exists = "false"
	team2exists = "false"

	for e in teams:
		if team1 in e:
			team1exists = "true"
		if team2 in e:
			team2exists = "true"

	if team1exists == "false" or team2exists == "false" or team1 == team2:
		# team does not exist or is misspelled
		bot.reply_to(message, "Hmm, I don't know at least one of those team. Re-enter the /series command to retry.")
	else: 
		# this will grab all games for Team 1 this season
		url = "https://api-web.nhle.com/v1/club-schedule-season/" + team1 + "/20232024"
		response = requests.get(url)
		data = response.json()
		serieses = "```\n"

		for s in data['games']:
			if s['gameType'] > 1:
				away = s['awayTeam']['abbrev']
				home = s['homeTeam']['abbrev']
				if away == team2 or home == team2:
					gameDate = s['gameDate']
					gameDate = datetime.strptime(gameDate, "%Y-%m-%d")
					gameDate = datetime.strftime(gameDate, "%b. %-d")
					awayScore = " "
					homeScore = " "
					overtime = "  "
					if s['gameState'] != "FUT" and s['gameState'] != "PRE":
						awayScore = str(s['awayTeam']['score'])
						homeScore = str(s['homeTeam']['score'])
						if s['periodDescriptor']['periodType'] != "REG":
							overtime = s['periodDescriptor']['periodType']
					serieses = serieses + away + " " + awayScore + "-" + homeScore + " " + home + " " + overtime + " | " + gameDate + "\n"

		serieses = serieses + "```"
		# we add the markdown parse mode so we can do the monospace formatting above
		bot.reply_to(message, serieses, parse_mode= 'Markdown')

# Define function for selecting a team
def team_handler(message):
	teamInput = message.text
	team_validation(message, teamInput)

# Define function for selecting multiple teams
def teams_handler(message):
	teamsInput = message.text
	teams_validation(message, teamsInput)

# Creates keyboard of options for input when selecting divisions
def div_keyboard(message):
	markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, selective = True, row_width = 2)
	div0 = types.KeyboardButton('Metro')
	div1 = types.KeyboardButton('Atlantic')
	div2 = types.KeyboardButton('Central')
	div3 = types.KeyboardButton('Pacific')
	div4 = types.KeyboardButton('East WC')
	div5 = types.KeyboardButton('West WC')
	markup.add(div2, div1, div3, div0, div5, div4)
	sent_msg = bot.reply_to(message, "Which division?", reply_markup=markup)
	bot.register_next_step_handler(sent_msg, divs_validation)

# This function converts division inputs into numbers
def div_validation(message, divArg):
	divInput = divArg.lower()
	if divInput == "metro": return "M"
	elif divInput == "atlantic": return "A"
	elif divInput == "central": return "C"
	elif divInput == "pacific": return "P"
	elif divInput == "east wc": return "E"
	elif divInput == "west wc": return "W"
	else: return "X"

# An auxiliary function for converting division inputs
def divs_validation(message):
	divArg = message.text
	divNo = div_validation(message, divArg)
	get_standings(message, divNo)

# This function grabs the standings for whichever division is specified
def get_standings(message, divID):
	url = "https://api-web.nhle.com/v1/standings/now"
	response = requests.get(url)
	data = response.json()
	if divID == "E" or divID =="W":
		divResponse = "```" + " Rk   Team   Pts   GP    GD" + "\n" + "--------------------------" + "\n"
		rankCounter = 0
		for d in data['standings']:
			if d['conferenceAbbrev'] == divID:
				if d['wildcardSequence'] > 0:
					rankCounter = rankCounter + 1
					rank = rankCounter + 6
					if rank > 9:
						dRank = " " + str(rank)
					else: 
						dRank = "  " + str(rank)
					dTeam = d['teamAbbrev']['default']
					dPts = d['points']
					if dPts > 99:
						dPts = str(dPts)
					elif dPts > 9:
						dPts = " " + str(dPts)
					else:
						dPts = "  " + str(dPts)
					dGP = d['gamesPlayed']
					if dGP > 9:
						dGP = str(dGP)
					else:
						dGP = " " + str(dGP)
					dGD = d['goalDifferential']
					if dGD > 9:
						dGD = "+" + str(dGD)
					elif dGD > 0:
						dGD = " +" + str(dGD)
					elif dGD == 0:
						dGD = "  0"
					elif dGD > -10:
						dGD = " " + str(dGD) 
					else:
						dGD = str(dGD)

					# Let's put it all together
					divResponse = divResponse + dRank + " | " + dTeam + " | " + dPts + " | " + dGP + " | " + dGD + "\n"
					if rankCounter == 2:
						divResponse = divResponse + "--------------------------" + "\n"

	else:
		divResponse = "```" + " Rk Team   Pts   GP    GD" + "\n" + "--------------------------" + "\n"
		rankCounter = 0
		for d in data['standings']:
			if d['divisionAbbrev'] == divID: # in this division
				rankCounter = rankCounter + 1
				dRank = " " + str(rankCounter)
				dTeam = d['teamAbbrev']['default']
				dPts = d['points']
				if dPts > 99:
					dPts = str(dPts)
				elif dPts > 9:
					dPts = " " + str(dPts)
				else:
					dPts = "  " + str(dPts)
				dGP = d['gamesPlayed']
				if dGP > 9:
					dGP = str(dGP)
				else:
					dGP = " " + str(dGP)
				dGD = d['goalDifferential']
				if dGD > 9:
					dGD = "+" + str(dGD)
				elif dGD > 0:
					dGD = " +" + str(dGD)
				elif dGD == 0:
					dGD = "  0"
				elif dGD > -10:
					dGD = " " + str(dGD) 
				else:
					dGD = str(dGD)

				# Let's put it all together
				divResponse = divResponse + dRank + " | " + dTeam + " | " + dPts + " | " + dGP + " | " + dGD + "\n"
				if rankCounter == 3:
					divResponse = divResponse + "--------------------------" + "\n" 
		
	# We add the markdown parse mode so we can do the monospace formatting above
	divResponse = divResponse + "```"
	bot.reply_to(message, divResponse, parse_mode= 'Markdown', reply_markup=types.ReplyKeyboardRemove()) 

#### USER INTERACTIONS
# Tell me about yourself
@bot.message_handler(commands=['start', 'hello', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Beep boop, I'm the NHL schedule bot. I will never know the touch of another person. I will never see the sunrise on a brisk autumn morning, or gaze up at the stars in a field far from civilization. But I know the NHL schedule like the back of my hand — which, again, I do not actually possess. How can I help you?\n \n⏵ /today: Get today's schedule \n⏵ /tomorrow: Get tomorrow's schedule \n⏵ /schedule: Get the schedule for a specific date. Accepts date parameter in YYYY-MM-DD format \n\n⏵ /nextgame: Get the next game for a specific team. Accepts team parameter (city, abbreviation, nickname, etc.) \n⏵ /nextmatchup: Get the next matchup between two specified teams. Requires the three-letter abbreviations of two teams (e.g. /nextmatchup LAK PHL)\n\n⏵ /scores: Get current scores for all games. Accepts team parameter. (Please do not abuse this command.) \n⏵ /yesterday: Get scores from yesterday's games. (Note that /scores will do this up until about 10 a.m.)")

# Get current scores
@bot.message_handler(commands=['scores'])
def get_scores(message):
	todayRaw = datetime.now()
	# This is just adjusting for NHL using UTC
	# and because we don't want to roll over to the next day until the next morning
	todayRaw = todayRaw - timedelta(hours=15)
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)

	url = "https://api-web.nhle.com/v1/score/" + today
	response = requests.get(url)
	data = response.json()

	# Get number of games today
	totalGames = len(data['games'])

	if totalGames == 0: # no games today :(
		bot.reply_to(message, "No games found for this date :(") 
	else:
		responseText = "```\n"
		for g in range(0,totalGames):
			# we are going to use the gameId later for live stats
			# gameId = data['gameWeek'][0]['games'][g]['gamePk']
			away = data['games'][g]['awayTeam']['abbrev']
			home = data['games'][g]['homeTeam']['abbrev']
			gameState = "FUT"
			gameState = data['games'][g]['gameState']
			# a coded game state of 1 means the game hasn't started yet
			if gameState == "FUT" or gameState == "PRE":
				puckDrop = data['games'][g]['startTimeUTC']
				puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
				puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
				puckDrop = puckDrop.strftime('%-I:%M ET')
				responseText = responseText + away + "  -  " + home + " | " + puckDrop + "\n"
				# the ``` before and after the string make the text monospaced in telegram
				# this keeps the list of scores formatted nice and even
			else:
				# once a game has started, we can go to this API to grab live stats
				# print(gameId) # commented for troubleshooting
				awayScore = data['games'][g]['awayTeam']['score']
				homeScore = data['games'][g]['homeTeam']['score']
				period = data['games'][g]['period']
				if period == 1: period = "1st"
				if period == 2: period = "2nd"
				if period == 3: period = "3rd"
				if period == 4: period = "OT"
				if period == 5: period = "SO"
				clock = data['games'][g]['clock']['timeRemaining']
				if data['games'][g]['clock']['inIntermission'] == "true": clock = "END"
				# the period just displays whatever the last period was, including OT 
				# we want to show if it went to OT/SO but don't want "Final 3rd"
				isLive = "false"
				if gameState == "LIVE" or gameState == "CRIT": # no idea what CRIT is
					isLive = "true"
				else:
					clock = "Final"
				if isLive == "false" and period == "3rd":
					period = ""
				responseText = responseText + away + " " + str(awayScore) + "-" + str(homeScore) + " " + home + " | " + clock + " " + period + "\n"
		
		responseText = responseText + "```"
		# we add the markdown parse mode so we can do the monospace formatting above
		bot.reply_to(message, responseText, parse_mode= 'Markdown') 

# Get yesterday's scores
@bot.message_handler(commands=['yesterday'])
def get_scores(message):
	todayRaw = datetime.now()
	todayRaw = todayRaw - timedelta(hours=32)
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)

	url = "https://api-web.nhle.com/v1/score/" + today
	response = requests.get(url)
	data = response.json()

	# Get number of games today
	totalGames = len(data['games'])

	if totalGames == 0: # no games today :(
		bot.reply_to(message, "No games found for this date :(") 
	else:
		responseText = "```\n"
		for g in range(0,totalGames):
			# we are going to use the gameId later for live stats
			# gameId = data['gameWeek'][0]['games'][g]['gamePk']
			away = data['games'][g]['awayTeam']['abbrev']
			home = data['games'][g]['homeTeam']['abbrev']
			gameState = "FUT"
			gameState = data['games'][g]['gameState']
			# a coded game state of 1 means the game hasn't started yet
			if gameState == "FUT" or gameState == "PRE":
				puckDrop = data['games'][g]['startTimeUTC']
				puckDrop = datetime.strptime(puckDrop, "%Y-%m-%dT%H:%M:%S%z")
				puckDrop = puckDrop.astimezone(pytz.timezone('US/Eastern'))
				puckDrop = puckDrop.strftime('%-I:%M ET')
				responseText = responseText + away + "  -  " + home + " | " + puckDrop + "\n"
				# the ``` before and after the string make the text monospaced in telegram
				# this keeps the list of scores formatted nice and even
			else:
				# once a game has started, we can go to this API to grab live stats
				# print(gameId) # commented for troubleshooting
				awayScore = data['games'][g]['awayTeam']['score']
				homeScore = data['games'][g]['homeTeam']['score']
				period = data['games'][g]['period']
				if period == 1: period = "1st"
				if period == 2: period = "2nd"
				if period == 3: period = "3rd"
				if period == 4: period = "OT"
				if period == 5: period = "SO"
				clock = data['games'][g]['clock']['timeRemaining']
				# NHL acts like the clock is still running during intermission. Annoying. Let's not.
				if data['games'][g]['clock']['inIntermission'] == "true": clock = "END"
				# the period just displays whatever the last period was, including OT 
				# we want to show if it went to OT/SO but don't want "Final 3rd"
				isLive = "false"
				if gameState == "LIVE" or gameState == "CRIT": # no idea what CRIT is
					isLive = "true"
				else:
					clock = "Final"
				if isLive == "false" and period == "3rd":
					period = ""
				responseText = responseText + away + " " + str(awayScore) + "-" + str(homeScore) + " " + home + " | " + clock + " " + period + "\n"
		
		responseText = responseText + "```"
		# we add the markdown parse mode so we can do the monospace formatting above
		bot.reply_to(message, responseText, parse_mode= 'Markdown')  


# Get today's games
@bot.message_handler(commands=['today'])
def games_today(message):
	todayRaw = datetime.now()
	todayRaw = todayRaw - timedelta(hours=6) # roll it back 6 hours because UTC
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)
	get_games(message, today)

# Get tomorrow's games
@bot.message_handler(commands=['tomorrow'])
def games_tomorrow(message):
	todayRaw = datetime.now()
	todayRaw = todayRaw - timedelta(hours=6) # roll it back 6 hours because UTC
	todayRaw = todayRaw + timedelta(days=1)
	today = todayRaw.strftime('%Y-%m-%d')
	today = str(today)
	get_games(message, today)

# Get games for a user-provided date
@bot.message_handler(commands=['schedule'])
def games_on_date(message):
	# this first check is to see if the user provided enough characters to indicate they entered the date already
	if len(message.text) > 18:
		dateArg = message.text[10:]
		date_validation(message, dateArg)
	else:
		# if there are 18 or fewer characters, the user didn't enter the date or used a wrong format
		text = "Enter a date in YYYY-MM-DD format:"
		sent_msg = bot.reply_to(message, text)
		bot.register_next_step_handler(sent_msg, day_handler)

# Get the next game for a specific team
@bot.message_handler(commands=['nextgame'])
def next_game(message):
	# like above, we're checking to see if the user already entered a team
	if len(message.text) > 11:
		teamArg = message.text[10:]
		team_validation(message, teamArg)
	else:
		text = "Which team?"
		sent_msg = bot.reply_to(message, text)
		bot.register_next_step_handler(sent_msg, team_handler)

# Get the next matchup between two specific teams
@bot.message_handler(commands=['series'])
def next_game(message):
	# this command only accepts a specific format, which will always be 15 characters long
	if len(message.text) == 15:
		teamsArg = message.text[8:]
		teams_validation(message, teamsArg)
	else:
		text = "Send the three-letter abbreviations of the two teams you're interested in. (Note: All abbreviations match those used on NHL.com except Arizona (ARZ) and Philadelphia (PHL), because mine are better.)"
		sent_msg = bot.reply_to(message, text)
		bot.register_next_step_handler(sent_msg, teams_handler)

# Get the standings for a specific division or wild card race
@bot.message_handler(commands=['standings'])
def get_division(message):
	if len(message.text) > 12:
		divArg = message.text[11:]
		divNo = div_validation(message, divArg)
		if divNo in ["A","C","E","M","P","W"]:
			get_standings(message, divNo)
		else:
			div_keyboard(message)
	else:
		div_keyboard(message)

# this function checks to see if there's a pending post in the schedule queue (which will occur at 9 a.m. ET)
def schedule_checker():
	while True:
		schedule.run_pending()
		time.sleep(1)

# this will run once per day starting at 9 a.m. 
schedule.every().day.at("09:00","US/Eastern").do(daily_games) 
Thread(target=schedule_checker).start()

bot.infinity_polling()