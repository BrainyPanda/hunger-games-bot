#Zlex Studios
# -*- coding: utf-8 -*-

#New feature: game files, stuff related to you only
#GAME FILES: Everything that isn't _ _ written into file.
#    gameStart: determine file name of the game (format: Guild - month/date/year - hour/minute)
#visually remove percentage of weaponry to give to clone.
#comment everything goddammit
#end game leaderboard being too much character to send bug
#rabid beaver kills text

#ALLIANCES:
#   - command: ask for alliance with someone
#   - command: pending requests for alliances
#   - command: accept alliance

#3 PLAYER: all rolls in tiers from 1-3
#   - 1/1/1 - free for all fight to the death
#   - 1/1/2 - two lowrolls fight to death, then midroll fights winner for 3-8 rounds
#   - 1/2/2 - two midrolls gang up on lowroll
#   - 1/3/3 - two highrollers sneak up on 3rd, doing damage and stealing weaponry
#   - 3/3/3 - find a very valuable tree with lots of one prize, they all take 6-8ish
#   - 2/3/3 - find 2 prizes, midroller does damage to both
#   - 1/2/3 - find a prize, highroller gets lots, midroller gets some, lowroller gets none

#EVENTS:
#   - Bloodlust gas: makes everyone fight to the death (very rare, only midgame and beyond) & single player (low chance) gas mask so don't have to fight
#   - Earthquake: everyone takes damage and loses some % of weaponry % arena opens up 15%
#   - Animals that are threatening everyone, probabilities change in single player
#   - Flood: weapon flow from one person to another & randomly attacking ppl from trees & food caught text change to seafood or relaxation in water & single player damage -> fish and such & weapons are harder to find
#       - No battles, arrow and bullets disabled
#   - Release giant wolves in arena proportional to days past (1-5, 5 wolves, 6-10, 4 wolves, etc.) Wolves have 0/0/0 stats

import os
import random
import discord
from dotenv import load_dotenv
import asyncio
import logging
import math
import datetime

from discord.ext import commands


path = "C:/Alex/Code/Discord/Hunger Games Bot"
STAT_MAX = 400
STARTING_HEALTH = 10.0
STARTING_DAMAGE = 1.5
DISCORD_MAX_MESSAGE_LENGTH = 2000
#specific for Lakeside HW Server
ADMIN_ROLE = "yeety"

#discord stuffs
_loop = asyncio.get_event_loop()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
logging.basicConfig(level=logging.INFO) #enable log errors

#set the command
bot = commands.Bot(command_prefix='!')

#Game Class: Stores basic information of each game on server. Takes one argument to initialize - the server it's being used in.
class Game():
    def __init__(self, server):
        self.server = server
        self.arenaEvents = [0, 0, 0, 0, 0] #Bloodlust, earthquake, animals, flood, giant wolves
        self.currentArenaEvent = -1 #Formula for likelihood: 4xday for BLoodlust, evenly distribute for rest
        self.allPlayers = []
        self.playersAfterGameStart = []
        self.gameStarted = False
        self.winnerDeclared = False
        self.dayOfGame = 0
        self.dayOngoing = False
        self.playersLeft = len(self.allPlayers)
        today = datetime.date.today()
        now = datetime.datetime.now()
        #creates the file name for storing the current game
        self.fileName = server.name + " - " + str(today.strftime("%b-%d-%Y")) + ", " + str(now.strftime("%H-%M")) + ".txt"

class Player():
    #Takes one argument to initialize - the name. Usually the discord nickname stripped of illegal file characters.
    def __init__(self, name):
        self.name = name
        self.displayName = "**" + name + "**"
        #ALL OVERALL STATS:
        #default statistics, all percentages
        self.stats = [40.0, 40.0, 40.0] #health, damage, resource, lucky
        self.wins = 0
        self.losses = 0
        #calculate the actual starting health with statistic factored in
        self.startingHealth = STARTING_HEALTH + (self.stats[0] / 100.0) * STARTING_HEALTH
        self.startingDamage = STARTING_DAMAGE + (self.stats[1] / 100.0) * STARTING_DAMAGE
        self.kills = 0
        self.deaths = 0
        self.daysAlive = 0
        self.daysDead = 0
        self.clonesCreated = 0
        #ALL STATS up to most recent stat change
        self.currentStatWins = 0
        self.currentStatLosses = 0
        self.currentStatKills = 0
        self.currentStatDeaths = 0
        self.currentStatDaysAlive = 0
        self.currentStatDaysDead = 0
        self.currentStatClonesCreated = 0
        #ALL STATS IN THE CURRENT GAME
        self.currentGameKills = 0
        self.currentGameDeaths = 0
        self.currentGameDaysAlive = 0
        self.currentGameDaysDead = 0
        self.currentGameHealth = 10.0
        self.currentGameDamage = 1.5
        self.currentGameAlive = True
        self.currentGameWeapons = [0, 0, 0] #Knife, Arrow ammo, Gun ammo
        self.currentGamePlace = 1
        self.currentGameClonesCreated = 0
        #random information storage variables
        self.cloneStats = [0, 0, 0]
        self.currentGameParent = None
        self.animalStatus = False
    def printStats(self, gameStarted):
        toReturn = "```" + self.name + "'s statistics: \n\n"
        #All lists are rows of information
        headerData = ["", "All Time", "Current Stat Setting"]
        winData = ["Wins:", str(self.wins), str(self.currentStatWins)]
        killsData = ["Kills:", str(self.kills), str(self.currentStatKills)]
        deathsData = ["Deaths:", str(self.deaths), str(self.currentStatDeaths)]
        daysAliveData = ["Days Alive:", str(self.daysAlive), str(self.currentStatDaysAlive)]
        daysDeadData = ["Days Dead:", str(self.daysDead), str(self.currentStatDaysDead)]
        clonesData = ["Clones Created:", str(self.clonesCreated), str(self.currentStatClonesCreated)]
        if gameStarted: #if a game has started, add another column of information by adding one piece of info to each row
            headerData.append("Current Game")
            winData.append("-")
            killsData.append(str(self.currentGameKills))
            deathsData.append(str(self.currentGameDeaths))
            daysAliveData.append(str(self.currentGameDaysAlive))
            daysDeadData.append(str(self.currentGameDaysDead))
            clonesData.append("-")
            healthData = ["Current Game Health", "-", "-", str(self.currentGameHealth)]
            damageData = ["Current Game Damage", "-", "-", str(self.currentGameDamage)]
            aliveData = ["Currently Alive?", "-", "-", str(self.currentGameAlive)]
        #consolidate data into one big 2D list
        data = [headerData, winData, killsData, deathsData, daysAliveData, daysDeadData, clonesData]
        if gameStarted:
            data.append(healthData)
            data.append(damageData)
            data.append(aliveData)
        #find the column width
        col_width = max(len(word) for row in data for word in row) + 4  #+4 spaces for padding between columns
        for i in range(len(data)):
            for j in range(len(data[i])):
                toReturn += str(data[i][j]) + " " * (col_width - len(str(data[i][j]))) #print the info, then add correct number of spaces
            toReturn += "\n"
        toReturn += "\n"
        toReturn += "Chosen Statistics: \n"
        toReturn += "Health: +" + str(self.stats[0]) + "%   (starts with " + str(round(self.startingHealth, 4)) + " Health)\n"
        toReturn += "Damage: +" + str(self.stats[1]) + "%   (starts with " + str(round(self.startingDamage, 4)) + " Damage)\n"
        toReturn += "Luckiness: +" + str(self.stats[2]) + "%\n"
        toReturn += "Minimum health to make a clone: " + str(self.cloneStats[0]) + "\n"
        toReturn += "Health to give to clone: " + str(self.cloneStats[1]) + " \n"
        toReturn += "Percentage of weaponry to give to clone: " + str(self.cloneStats[2]) + "% \n"
        toReturn += "\n"
        if gameStarted:
            toReturn += "Current Weaponry: Knives: " + str(self.currentGameWeapons[0]) + ".  Arrows left: " + str(self.currentGameWeapons[1]) + ".  Bullets left: " + str(self.currentGameWeapons[2]) + ". \n```"
        else:
            toReturn += "```"
        return toReturn
    def savePlayer(self):
        #saves a player's information into a file, if the player isn't a clone or an animal
        if self.currentGameParent == None and not self.animalStatus:
            self.name = ''.join([i if ord(i) < 128 else ' ' for i in self.name])
            self.name = ''.join([i if i != "<" and i != ">" and i != ":" and i != '"' and i != "/" and i != "|" and i != "?" and i != "*" else ' ' for i in self.name]) #missing taking out \
            pathName = self.name
            self.displayName = "**" + self.name + "**"
            toWrite = self.name + "\n"
            toWrite += str(self.wins) + "\n"
            toWrite += str(self.losses) + "\n"
            toWrite += str(self.stats[0]) + "\n"
            toWrite += str(self.stats[1]) + "\n"
            toWrite += str(self.stats[2]) + "\n"
            toWrite += str(self.startingHealth) + "\n"
            toWrite += str(self.startingDamage) + "\n"
            toWrite += str(self.kills) + "\n"
            toWrite += str(self.deaths) + "\n"
            toWrite += str(self.daysAlive) + "\n"
            toWrite += str(self.daysDead) + "\n"
            toWrite += str(self.currentStatWins) + "\n"
            toWrite += str(self.currentStatLosses) + "\n"
            toWrite += str(self.currentStatKills) + "\n"
            toWrite += str(self.currentStatDeaths) + "\n"
            toWrite += str(self.currentStatDaysAlive) + "\n"
            toWrite += str(self.currentStatDaysDead) + "\n"
            toWrite += str(self.currentGameKills) + "\n"
            toWrite += str(self.currentGameDeaths) + "\n"
            toWrite += str(self.currentGameDaysAlive) + "\n"
            toWrite += str(self.currentGameDaysDead) + "\n"
            toWrite += str(self.currentGameHealth) + "\n"
            toWrite += str(self.currentGameDamage) + "\n"
            toWrite += str(self.currentGameAlive) + "\n"
            toWrite += str(self.currentGameWeapons[0]) + "\n"
            toWrite += str(self.currentGameWeapons[1]) + "\n"
            toWrite += str(self.currentGameWeapons[2]) + "\n"
            toWrite += str(self.currentGamePlace) + "\n"
            toWrite += str(self.cloneStats[0]) + "\n"
            toWrite += str(self.cloneStats[1]) + "\n"
            toWrite += str(self.cloneStats[2]) + "\n"
            toWrite += str(self.clonesCreated) + "\n"
            toWrite += str(self.currentStatClonesCreated) + "\n"
            toWrite += str(self.currentGameClonesCreated) + "\n"
            f = open(os.path.join(path, pathName), "w+")
            f.write(toWrite)
            f.close()
            print("Player saved! Name: " + str(pathName) + " Wins: " + str(self.wins) + ".     Stats: " + str(self.stats) + ".\n\n\n ")
            return pathName
        else:
            print("Saving failed (Clone or animal).")
    def loadPlayer(self):
        #loads a player from file provided by the filename attribute, which would set by having the name set to the filename
        if self.currentGameParent == None and not self.animalStatus:
            pathName = self.name
            try:
                f = open(os.path.join(path, pathName), "r")
                loadedStats = f.read().splitlines()
                f.close()
            except:
                return False
            self.wins = int(loadedStats[1])
            self.losses = int(loadedStats[2])
            self.stats[0] = float(loadedStats[3])
            self.stats[1] = float(loadedStats[4])
            self.stats[2] = float(loadedStats[5])
            self.startingHealth = float(loadedStats[6])
            self.startingDamage = float(loadedStats[7])
            self.kills = int(loadedStats[8])
            self.deaths = int(loadedStats[9])
            self.daysAlive = int(loadedStats[10])
            self.daysDead = int(loadedStats[11])
            self.currentStatWins = int(loadedStats[12])
            self.currentStatLosses = int(loadedStats[13])
            self.currentStatKills = int(loadedStats[14])
            self.currentStatDeaths = int(loadedStats[15])
            self.currentStatDaysAlive = int(loadedStats[16])
            self.currentStatDaysDead = int(loadedStats[17])
            self.currentGameKills = int(loadedStats[18])
            self.currentGameDeaths = int(loadedStats[19])
            self.currentGameDaysAlive = int(loadedStats[20])
            self.currentGameDaysDead = int(loadedStats[21])
            self.currentGameHealth = float(loadedStats[22])
            self.currentGameDamage = float(loadedStats[23])
            self.currentGameAlive = bool(loadedStats[24])
            self.currentGameWeapons[0] = int(loadedStats[25])
            self.currentGameWeapons[1] = int(loadedStats[26])
            self.currentGameWeapons[2] = int(loadedStats[27])
            self.currentGamePlace = int(loadedStats[28])
            self.cloneStats[0] = float(loadedStats[29])
            self.cloneStats[1] = float(loadedStats[30])
            self.cloneStats[2] = float(loadedStats[31])
            self.clonesCreated = int(loadedStats[32])
            self.currentStatClonesCreated = int(loadedStats[33])
            self.currentGameClonesCreated = int(loadedStats[34])
            self.displayName = "**" + self.name + "**"
            return True
        else:
            print("Loading clone failed (clones aren't saved)")
            return False
    def changeStats(self, newHealth, newDamage, newLucky):
        #changes the statistics
        if newHealth < 0 or newDamage < 0 or newLucky < 0:
            return "Error: At least one of your variables is negative!"
        global STAT_MAX
        if newHealth + newDamage + newLucky > STAT_MAX:
            return "Error: Your variables sum to greater than " + str(STAT_MAX) + ". The limit is " + str(STAT_MAX) + "."
        self.currentStatWins = 0
        self.currentStatLosses = 0
        self.currentStatKills = 0
        self.currentStatDeaths = 0
        self.currentStatDaysAlive = 0
        self.currentStatDaysDead = 0
        self.currentStatClonesCreated = 0
        self.stats = [float(newHealth), float(newDamage), float(newLucky)]
        self.startingHealth = 10.0 + (self.stats[0] / 100.0) * 10.0
        self.startingDamage = 1.5 + (self.stats[1] / 100.0) * 1.5
        return "Changes successful!"
    def changeCloneStats(self, newHealth, newHealthToSplit, weaponryPercentage):
        #changes the clone statistics. 
        if newHealth < 0 or weaponryPercentage < 0 or newHealthToSplit < 0:
            return "Error: At least one of your variables is negative!"
        if newHealth <= newHealthToSplit:
            return "Error: Your health to split at is lower than the health you will give to the clone."
        if weaponryPercentage > 100:
            return "Error: Your weaponry percentage can't be above 100."
        self.currentStatWins = 0
        self.currentStatLosses = 0
        self.currentStatKills = 0
        self.currentStatDeaths = 0
        self.currentStatDaysAlive = 0
        self.currentStatDaysDead = 0
        self.currentStatClonesCreated = 0
        self.cloneStats = [float(newHealth), float(newHealthToSplit), float(weaponryPercentage)]
        return "Changes successful!"
    def die(self, killer, game): #if killer is None, then it was single player death.
        #all death related stuff
        self.currentGameDeaths += 1
        self.currentStatDeaths += 1
        self.deaths += 1
        self.currentGameAlive = False
        response = ""
        if killer != None:
            response = "\n " + killer.displayName + " killed " + self.displayName + " and gained all their weaponry. "
        self.currentGamePlace = game.playersLeft
        game.playersLeft -= 1
        if killer != None:
            killer.currentGameKills += 1
            killer.currentStatKills += 1
            killer.kills += 1
            killer.currentGameWeapons[1] += self.currentGameWeapons[1]
            killer.currentGameWeapons[2] += self.currentGameWeapons[2]
            killer.currentGameWeapons[0] += self.currentGameWeapons[0]
            if killer.name == "Giant Wolf" and self.name == "Giant Wolf": #unenrage giant wolf if it's two giant wolves fighting each other
                killer.currentGameDamage = killer.currentGameDamage / 4
                killer.currentGameDamage = round(killer.currentGameDamage, 4)
        return response
    def becomeClone(self, parentPlayer, healthToSplit, weaponryPercentage):
        #after player is initialized, this is called for player to become clone.
        #Takes in the parent player that is being cloned, the health to split, and the weaponry percentage to take.
        healthToSplit = round(healthToSplit, 4)
        self.currentGameParent = parentPlayer
        parentPlayer.clonesCreated += 1
        parentPlayer.currentStatClonesCreated += 1
        parentPlayer.currentGameClonesCreated += 1
        self.name = parentPlayer.name + " " + str(parentPlayer.currentGameClonesCreated + 1) + ".0"
        self.displayName = "**" + self.name + "**"
        response = parentPlayer.displayName + " created " + self.displayName
        self.stats = []
        for i in range(len(parentPlayer.stats)):
            self.stats.append(parentPlayer.stats[i])
        self.startingHealth = float(healthToSplit)
        self.startingHealth = round(self.startingHealth, 4)
        response += " with " + str(self.startingHealth) + " Health, "
        parentPlayer.currentGameHealth -= float(healthToSplit)
        parentPlayer.currentGameHealth = round(parentPlayer.currentGameHealth, 4)
        #basic stat stuff
        self.startingDamage = parentPlayer.startingDamage
        self.kills = 0
        self.deaths = 0
        self.daysAlive = 0
        self.daysDead = 0
        self.currentStatWins = 0
        self.currentStatLosses = 0
        self.currentStatKills = 0
        self.currentStatDeaths = 0
        self.currentStatDaysAlive = 0
        self.currentStatDaysDead = 0
        self.currentGameKills = 0
        self.currentGameDeaths = 0
        self.currentGameDaysAlive = 0
        self.currentGameDaysDead = 0
        self.currentGameHealth = float(healthToSplit)
        self.currentGameDamage = parentPlayer.startingDamage
        self.currentGameAlive = True
        #weaponry stuff
        self.currentGameWeapons = [0, 0, 0] #Knife, Arrow ammo, Gun ammo
        knivesToGive = int(parentPlayer.currentGameWeapons[0] * (weaponryPercentage / 100.0))
        response += "armed with " + str(knivesToGive) + " knives, "
        arrowsToGive = int(parentPlayer.currentGameWeapons[1] * (weaponryPercentage / 100.0))
        response += str(arrowsToGive) + " arrows, "
        bulletsToGive = int(parentPlayer.currentGameWeapons[2] * (weaponryPercentage / 100.0))
        response += "and " + str(bulletsToGive) + " bullets. "
        self.currentGameWeapons[0] += knivesToGive
        parentPlayer.currentGameWeapons[0] -= knivesToGive
        self.currentGameWeapons[1] += arrowsToGive
        parentPlayer.currentGameWeapons[1] -= arrowsToGive
        self.currentGameWeapons[2] += bulletsToGive
        parentPlayer.currentGameWeapons[2] -= bulletsToGive
        self.currentGamePlace = 1
        return response

@bot.event
async def on_ready(): #init bot
    print(str(bot.user.name) + ' has connected to Discord! ')
    bot.gamesStarted = []

@bot.event
async def on_command_error(ctx, error): #any error when running commands
    if isinstance(error, commands.errors.CheckFailure): #wrong role for role-locked commands
        await ctx.send("You do not have the correct role for this command.")
    else:
        print(error) #prints to command console what error was
    if not isinstance(error, commands.errors.CommandNotFound): #if the command is found, but there's an error, then command crashed. Send some text as a story for why game suddenly stopped.
        await ctx.send("COVID-19 was detected in the arena! The game has been forceably ended and robots have been deployed for deep cleaning. Please stand by. ")

def writeToFile(fileName, toWrite): #function used to write to a certain file. Takes the file name and what to write as imputs
    f = open(os.path.join(path, fileName), "a")
    f.write("\n" + toWrite)
    f.close()
    return True #usually useless

#calculates full damage actor will do in battle
def calcDamage(finalActor, battle = True):
    damage = finalActor.currentGameDamage
    finalDamage = damage
    weaponFound = False
    if finalActor.currentGameWeapons[0] > 0: #following code is to nerf knives in the endgame
        if finalActor.currentGameWeapons[0] <= 14: #point of interception: (14.076, 3.815) - this is after knives are dealing more damage than bullets and arrows
            finalDamage = damage * (1 + 0.2 * finalActor.currentGameWeapons[0])
        else:
            finalDamage = damage * (math.log2(finalActor.currentGameWeapons[0]))
        theirWeapon = "their knife"
        weaponFound = True
    if finalActor.currentGameWeapons[1] > 0 and finalActor.currentGameWeapons[0] < 7: #if more than 7 knives, knives will deal more damage
        finalDamage = damage * 2.25
        theirWeapon = "their bow"
        weaponFound = True
    if finalActor.currentGameWeapons[2] > 0 and finalActor.currentGameWeapons[0] < 11: #if more than 11 knives, knives will deal more damage
        finalDamage = damage * 3.0
        theirWeapon = "their gun"
        weaponFound = True
    if not weaponFound: #they have no weapons, so they use their base damage and have their fist
        theirWeapon = "their fist"
    if finalActor.name == "Giant Wolf":
        theirWeapon = "their sharp claws"
    #kill streak - (kills - 1)/2, at 3+ kills
    factor = float((finalActor.currentGameKills - 1)/2)
    if factor < 1:
        factor = 1
    finalDamage *= factor
    finalDamage = round(finalDamage, 4)
    return finalDamage, theirWeapon

#calculates how much the damage is limited by roll. Only a function so it's easier to balance
def limitDamage(originalDamage, roll):
    converter = roll
    if roll > 83: #keep damage dealt to 100% cap
        converter = 83
    if converter >= 33 and converter <= 83:
        converter = ((converter - 33)) + 50
    finalDamage = originalDamage * (converter / 100)
    finalDamage = round(finalDamage, 4) #rounding so numbers don't get ugly
    return finalDamage

#removes the weaponry used from armory of player, based on number of weaponry the player has
def removeWeaponUsedBattle(actor):
    if actor.currentGameWeapons[2] > 0 and actor.currentGameWeapons[0] < 11: #remove a bullet from weaponry stock because it was used. At 11, bullets are more damaging so they would be used
        actor.currentGameWeapons[2] -= 1
    elif actor.currentGameWeapons[1] > 0 and actor.currentGameWeapons[0] < 7: #remove an arrow from weaponry stock because it was used. At 7, knives are more damaging so they would be used
        actor.currentGameWeapons[1] -= 1

#calculate percentage arena is closed. factor is the factor to multiply the default by, limit is if to limit percentage to between 0 and 100
def calcArenaClosure(currentGame, factor = 5, limit = False):
    toReturn = (currentGame.dayOfGame - (currentGame.arenaEvents[1] * 3)) * factor #calculate percentage of arena closed - (dayOfGame - 3 * how many earthquakes have happened this game) * factor
    if limit:
        if toReturn < 0: #limit percentage between 0 and 100
            toReturn = 0
        if toReturn > 100:
            toReturn = str(100)
    return toReturn

#determines the prize that the actor found.
def determinePrize(actor, foodToUse):
    prize = random.randint(1, 4)
    amount = random.randint(2, 4) + int(actor.stats[1]/100.0)
    healingAmount = random.randint(2, 6) + int(actor.stats[0]/100.0)
    if prize < 4:
        weapon = random.randint(1, 10)
        if weapon <= 3:
            prize = "a knife"
            weaponPrize = "knife"
        elif weapon <= 7:
            prize = str(amount) + " arrows"
            weaponPrize = "bow"
        elif weapon <= 10:
            prize = str(amount) + " bullets"
            weaponPrize = "gun"
    else:
        prize = str(healingAmount) + " " + foodToUse
        weaponPrize = "heal"
    return prize, weaponPrize, amount, healingAmount

#Runs a battle between two actors.
#finalActors: list of Players that are going to be doing the fighting
#verbToUse: The verb to use as an excuse for why they're fighting
#currentGame: The Game Object that this battle is going to be for
#rounds: number of rounds they'll go. if -1, fight to death.
#returns a list with the text of the battle, one line per element
def battle(finalActors, verbToUse, currentGame, rounds = -1):
    responses = []
    if currentGame.currentArenaEvent != 0: #if the arena even isn't gas that makes everyone fight to death, it's an accident. otherwise it's on purpose
        toAccident = "accidentally "
    else:
        toAccident = "purposefully "
    response = finalActors[0].displayName + " " + toAccident + verbToUse + " " + finalActors[1].displayName + ". " + finalActors[1].displayName + " is mad. "
    if currentGame.currentArenaEvent == 2:
        response = finalActors[0].displayName + " " + toAccident + "shoves " + finalActors[1].displayName + " into some rabid beavers. After barely escaping their grasp, " + finalActors[1].displayName + " seeks revenge. "
    if rounds == -1:
        response += "This will be a fight to the death."
    responses.append(response)
    response2 = "_ _"
    responses.append(response2)
    roundsPassed = 0
    if finalActors[0].name == "Giant Wolf" and finalActors[1].name == "Giant Wolf" and rounds == -1: #to speed up wolf vs wolf battles.
        response = "\nThe Giant Wolf, seeing that it is opposed by one of its own kind, becomes very angry and gains x4 damage. The other Giant Wolf also gains x4 damage."
        finalActors[0].currentGameDamage *= 4
        finalActors[1].currentGameDamage *= 4
        finalActors[0].currentGameDamage = round(finalActors[0].currentGameDamage, 4)
        finalActors[1].currentGameDamage = round(finalActors[1].currentGameDamage, 4)
        responses.append(response)
        responses.append("_ _")
    if rounds == -1: #fight to death
        rounds = 1000000000000000
    while (roundsPassed < rounds and finalActors[0].currentGameHealth > 0 and finalActors[1].currentGameHealth > 0): #keep doing rounds until round limit reached or someone dies
        response = ""
        #needs greater than 100 to counter - opponent will miss no matter what
        #84+ means 100% damage dealt
        #33-83 will scale down damage by percentage (number - 33) * 2
        #1-33 - no damage dealt, they were unlucky and missed
        finalDamage, theirWeapon = calcDamage(finalActors[0], battle = True)
        finalDamage2, theirWeapon2 = calcDamage(finalActors[1], battle = True)
        #each player rolls a number. Damage stat/12 is then added to this roll.
        newNumbers = []
        for j in range(len(finalActors)):
            newNumber = random.randint(1, 100)
            newNumber = newNumber + (finalActors[j].stats[1] / 12.0)
            newNumbers.append(newNumber)
        print(newNumbers) #for debugging, prints to command prompt
        #calculate final damage output based on roll
        finalDamage = limitDamage(finalDamage, newNumber[0])
        finalDamage2 = limitDamage(finalDamage, newNumber[1])
        #case work for scenarios based on rolls, with proper text for the storyline
        if newNumbers[0] <= 33 and newNumbers[1] <= 33: #both lowroll, both miss
            response += finalActors[0].displayName + " attempts to use " + theirWeapon + ", while " + finalActors[1].displayName + " attempts to use " + theirWeapon2 + ". Both somehow wildly miss each other. "
        elif newNumbers[0] <= 33 and newNumbers[1] > 33: #one lowrolls and misses, second deals damage
            response += finalActors[0].displayName + " attempts to use " + theirWeapon + ", but " + finalActors[1].displayName + " is too fast and dodges. " + finalActors[1].displayName + " then uses " + theirWeapon2 + " to land a solid hit for " + str(finalDamage2) + " damage. "
            finalActors[0].currentGameHealth -= finalDamage2
            finalActors[0].currentGameHealth = round(finalActors[0].currentGameHealth, 4)
            if finalActors[0].currentGameHealth <= 0: #first guy died, so second player gets a kill and all weaponry
                response += finalActors[0].die(finalActors[1], currentGame)
        elif newNumbers[0] > 33 and newNumbers[1] <= 33: #first deals damage, second guy lowrolls and misses
            response += finalActors[0].displayName + " uses " + theirWeapon + " and lands a solid hit for " + str(finalDamage) + ". " + finalActors[1].displayName + " misses with " + theirWeapon2 + " due to the pain inflicted. "
            finalActors[1].currentGameHealth -= finalDamage
            finalActors[1].currentGameHealth = round(finalActors[1].currentGameHealth, 4)
            if finalActors[1].currentGameHealth <= 0: #second guy died, so first player gets a kill and all weaponry
                response += finalActors[1].die(finalActors[0], currentGame)
        elif newNumbers[0] < 100 and newNumbers[1] < 100: #both players roll high enough to deal damage to each other
            if finalActors[0].currentGameHealth - finalDamage2 <= 0 and finalActors[1].currentGameHealth - finalDamage <= 0: #prevents double death
                decidor = 0
                decidor2 = 0
                while decidor == decidor2: #decide randomly, with luck stat helping, who will be able to deal damage and kill the other.
                    decidor = random.randint(1, 100)
                    decidor = decidor + (finalActors[0].stats[2] / 12.0)
                    decidor2 = random.randint(1, 100)
                    decidor2 = decidor2 + (finalActors[1].stats[2] / 12.0)
                if decidor > decidor2: #highest roll wins. Here first guy rolled higher
                    response += finalActors[0].displayName + " uses " + theirWeapon + " and lands a solid hit for " + str(finalDamage) + ". " + finalActors[1].displayName + " misses with " + theirWeapon2 + " due to the pain inflicted. "
                    finalActors[1].currentGameHealth -= finalDamage
                    finalActors[1].currentGameHealth = round(finalActors[1].currentGameHealth, 4)
                    if finalActors[1].currentGameHealth <= 0:
                        response += finalActors[1].die(finalActors[0], currentGame)
                else: #second guy rolled higher
                    response += finalActors[0].displayName + " attempts to use " + theirWeapon + ", but " + finalActors[1].displayName + " is too fast and dodges. " + finalActors[1].displayName + " then uses " + theirWeapon2 + " to land a solid hit for " + str(finalDamage2) + " damage. "
                    finalActors[0].currentGameHealth -= finalDamage2
                    finalActors[0].currentGameHealth = round(finalActors[0].currentGameHealth, 4)
                    if finalActors[0].currentGameHealth <= 0:
                        response += finalActors[0].die(finalActors[1], currentGame)
            else: #they both hit each other
                response += finalActors[0].displayName + " uses " + theirWeapon + " and lands a solid hit for " + str(finalDamage) + ", while at the same time " + finalActors[1].displayName + " uses " + theirWeapon2 + " to land a solid hit for " + str(finalDamage2) + " damage. "
                finalActors[0].currentGameHealth -= finalDamage2
                finalActors[0].currentGameHealth = round(finalActors[0].currentGameHealth, 4)
                if finalActors[0].currentGameHealth <= 0:
                    response += finalActors[0].die(finalActors[1], currentGame)
                finalActors[1].currentGameHealth -= finalDamage
                finalActors[1].currentGameHealth = round(finalActors[1].currentGameHealth, 4)
                if finalActors[1].currentGameHealth <= 0:
                    response += finalActors[1].die(finalActors[0], currentGame)
        elif newNumbers[0] < 100 and newNumbers[1] >= 100: #first guy tries to deal damage, but second guy rolled high and a shoop falls from the sky, blocking all damage. second guy then deals damage
            response += finalActors[0].displayName + " uses " + theirWeapon + ", but suddenly a shoop falls from the sky and gets in the way. The damage is negated. " + finalActors[1].displayName + " then uses " + theirWeapon2 + " to land a solid hit for " + str(finalDamage2) + " damage. "
            finalActors[0].currentGameHealth -= finalDamage2
            finalActors[0].currentGameHealth = round(finalActors[0].currentGameHealth, 4)
            if finalActors[0].currentGameHealth <= 0:
                response += finalActors[0].die(finalActors[1], currentGame)
        elif newNumbers[0] >= 100 and newNumbers[1] < 100: #reverse of case above
            response += finalActors[1].displayName + " uses " + theirWeapon + ", but suddenly a shoop falls from the sky and gets in the way. The damage is negated. " + finalActors[0].displayName + " then uses " + theirWeapon + " to land a solid hit for " + str(finalDamage) + " damage. "
            finalActors[1].currentGameHealth -= finalDamage
            finalActors[1].currentGameHealth = round(finalActors[1].currentGameHealth, 4)
            if finalActors[1].currentGameHealth <= 0:
                response += finalActors[1].die(finalActors[0], currentGame)
        elif newNumbers[0] >= 100 and newNumbers[1] >= 100: #both highroll and all damage is negated
            response += finalActors[0].displayName + " uses " + theirWeapon + ", while at the same time " + finalActors[1].displayName + " uses " + theirWeapon2 + ". Luckily for both, a heavy wind blows and all damage is negated. "
            response += "\n\n"
        removeWeaponUsedBattle(finalActors[0])
        removeWeaponUsedBattle(finalActors[1])
        #usual battle output response is built here
        response += "\n" + finalActors[0].displayName + ":  Health: " + str(finalActors[0].currentGameHealth) + ".  Knives: " + str(finalActors[0].currentGameWeapons[0]) + ".  Arrows left: " + str(finalActors[0].currentGameWeapons[1]) + ".  Bullets left: " + str(finalActors[0].currentGameWeapons[2]) + ". "
        response += "\n" + finalActors[1].displayName + ":  Health: " + str(finalActors[1].currentGameHealth) + ".  Knives: " + str(finalActors[1].currentGameWeapons[0]) + ".  Arrows left: " + str(finalActors[1].currentGameWeapons[1]) + ".  Bullets left: " + str(finalActors[1].currentGameWeapons[2]) + ". " 
        responses.append(response)
        response2 = "_ _\n_ _" #_ _ prints an empty line in discord
        responses.append(response2)
        if finalActors[0].currentGameHealth > 0 and finalActors[1].currentGameHealth > 0 and rounds != 1000000000000000: #if not fighting to the death and both are alive, either fighter can offer to end fight
            toOffer = random.randint(1, 100)
            offer = 0
            if roundsPassed == rounds - 1 or toOffer < 10: #if it is the last round, the guarantee offer. otherwise 10%
                offer = random.randint(1, 2) #choose who to offer
                response = "\n" + finalActors[offer - 1].displayName + " offers to end the fighting. "
            if roundsPassed == rounds - 1 and offer == 1: #agree to offer if it is the last round
                response += finalActors[1].displayName + " agrees. "
            elif roundsPassed == rounds - 1 and offer == 2:
                response += finalActors[0].displayName + " agrees. "
            elif offer == 1: #disagree the offer because it's not the last round
                response += finalActors[1].displayName + " disagrees and wants to keep fighting. "
            elif offer == 2:
                response += finalActors[0].displayName + " disagrees and wants to keep fighting. "
            if roundsPassed == rounds - 1 or toOffer < 10:
                responses.append(response)
        roundsPassed += 1
    return responses

#HUNGER GAMES: #each player gets a file with all their stats so they keep stats when bot is upgraded.
#start: starts the game, creates a Game instance and all the Player instances ADMIN ONLY
@bot.command(name='gameStart', pass_context = True, help="starts the Games, ADMIN ONLY", aliases=['start'])
@commands.has_role(ADMIN_ROLE)
async def gameStart(ctx):
    alreadyRunning = False #only one game per server allowed - could be removed in future
    for game in bot.gamesStarted:
        if game.server == ctx.message.guild and game.gameStarted:
            alreadyRunning = True
    if alreadyRunning:
        response = "The Games are already running! "
    else:
        newGame = Game(ctx.message.guild)
        bot.gamesStarted.append(newGame) #bot.gamesStarted is the list of games currently the bot is running
        playerNames = []
        role = discord.utils.find(lambda r: r.name == "Hunger Games", ctx.message.guild.roles) #get all the people who have the Hunger Games role
        for member in ctx.message.guild.members:
            if not member.bot and role in member.roles:
                playerNames.append(member.display_name)
        for i in range(len(playerNames)):
            #take out all file illegal characters in the following two lines
            playerNames[i] = ''.join([i if ord(i) < 128 else ' ' for i in playerNames[i]])
            playerNames[i] = ''.join([i if i != "<" and i != ">" and i != ":" and i != '"' and i != "/" and i != "|" and i != "?" and i != "*" else ' ' for i in playerNames[i]]) #missing taking out \
            print(playerNames[i])
            newPlayer = Player(playerNames[i])
            success = newPlayer.loadPlayer() #try and load the player. If this returns false, simply save the created player as a new player
            if not success:
                newPlayer.savePlayer()
            newGame.allPlayers.append(newPlayer)
        response = "The Games have begun! Everyone is now armed with a bow and an empty gun. It is your job to find the ammunition. Good luck to all! "
        newGame.gameStarted = True
        for player in newGame.allPlayers: #initial player stats
            player.startingHealth = STARTING_HEALTH + (player.stats[0] / 100.0) * STARTING_HEALTH
            player.startingHealth = round(player.startingHealth, 4)
            player.startingDamage = STARTING_DAMAGE + (player.stats[1] / 100.0) * STARTING_DAMAGE
            player.startingDamage = round(player.startingDamage, 4)
            player.currentGameKills = 0
            player.currentGameDeaths = 0
            player.currentGameDaysAlive = 0
            player.currentGameDaysDead = 0
            player.currentGameHealth = STARTING_HEALTH + (player.stats[0] / 100.0) * STARTING_HEALTH
            player.currentGameHealth = round(player.currentGameHealth, 4)
            player.currentGameDamage = STARTING_DAMAGE + (player.stats[1] / 100.0) * STARTING_DAMAGE
            player.currentGameDamage = round(player.currentGameDamage, 4)
            player.currentGameAlive = True
            player.currentGameWeapons = [0, 0, 0]
            player.currentGamePlace = 1
            player.currentGameClonesCreated = 0
            player.savePlayer()
        newGame.winnerDeclared = False
        newGame.dayOfGame = 1            
        newGame.playersLeft = len(newGame.allPlayers)
        for player in newGame.allPlayers: #save all players - necessary since lots of currentGame statistics changed
            player.savePlayer()
        f = open(os.path.join(path, newGame.fileName), "w+")
        f.close()
    await ctx.send(response)
    f = open(os.path.join(path, newGame.fileName), "a")
    f.write(newGame.fileName)
    f.close()
    writeToFile(newGame.fileName, response)
#next: the next day ADMIN ONLY. Can take a parameter, dayCounter, which sets how many days we're going to
@bot.command(name='gameNextDay', pass_context = True, help="plays the next day of the Games, enter a number to play that many days. -1 for auto. ADMIN ONLY", aliases=['nextDay'])
@commands.has_role(ADMIN_ROLE)
async def gameNextDay(ctx, dayCounter = 1):
    currentGame = 0
    for game in bot.gamesStarted:
        if game.server == ctx.message.guild:
            currentGame = game
    daysPast = 0
    limit = dayCounter
    if dayCounter < 0:
        limit = 10000000000
    while daysPast < limit:
        if daysPast != 0: #after first day, all subsequent days have a pause at beginning to make reading easier
            await asyncio.sleep(4)
        if currentGame.dayOngoing:
            response = "There's already a day running!"
            await ctx.send(response)
            return 0 #kill the command if there's already a day running
        currentGame.dayOngoing = True
        verbs = ["trips", "runs into", "falls on", "kicks", "sneezes on", "bites", "fries"]
        foods = ["apples", "steaks", "mozzarella sticks", "pineapple pizzas", "LaCroixs", "packets of dried instant ramen", "boba teas", "fried chickens"]
        surprises = [["mouse trap", "closes"], ["wild harribo gummy bear", "cronches"], ["passing pterodactyl", "lunges"], 
                     ["developer", "codes a bug"], ["star-nosed mole", "eats"], ["zombie fried-chicken", "slices their stomach open to retrieve its brethren"]]
        if not currentGame.gameStarted: #the day needs a game to run on
            response = "There is no ongoing Game!"
            await ctx.send(response)
            return 0
        elif currentGame.winnerDeclared:
            return 1 #there's a winner, so no more days are needed
        percentageClosed = calcArenaClosure(currentGame, factor = 5)
        await ctx.send("Day " + str(currentGame.dayOfGame) + "! " + str(percentageClosed) + "% of arena is closed! ")
        writeToFile(currentGame.fileName, "Day " + str(currentGame.dayOfGame) + "! " + str(percentageClosed) + "% of arena is closed! ")
        await asyncio.sleep(1.5)
        response2 = "_ _"
        await ctx.send(response2)
        actorsRemaining = [] #get all the alive players into this list, then shuffle it
        for player in currentGame.allPlayers:
            if player.currentGameAlive:
                actorsRemaining.append(player)
        random.shuffle(actorsRemaining)
        #arena probability: calculate if arena is going to happen today
        arenaEvent = random.randint(1, 100)
        if arenaEvent < 17: #around 1 in 6 days (4-5 for 30 day games)
            await asyncio.sleep(1) #extra waiting to build suspense before arena event is displayed
            eventToChoose = random.randint(1, 100) #roll arena event
            print("ARENA EVENT: " + str(eventToChoose))
            gasProbability = 0
            if currentGame.dayOfGame >= 10: #fight to the death gas can't happen before day 10 (it's really boring when it does). Afterwards, scales based on day
                gasProbability = currentGame.dayOfGame * 2
            remainder = 100 - gasProbability
            toEach = int(remainder / 4) #divide remaining probability among the remaining 
            if currentGame.dayOfGame > 25: #no wolves will spawn, so remainder should be divided among 3 arena events instead of four
                toEach = int(remainder / 3)
            if eventToChoose < gasProbability + 1:
                currentGame.currentArenaEvent = 0
                response = "**ARENA EVENT:** A gas fills the arena... Everyone now hungers for blood! It shall be spilt! "
            elif eventToChoose < gasProbability + 1 + toEach:
                currentGame.currentArenaEvent = 1
                response = "**ARENA EVENT:** A tremor shakes the arena early in the morning. "
                await ctx.send(response)
                writeToFile(currentGame.fileName, response)
                await asyncio.sleep(3)
                #for all alive characters: deal same damage, and make them lose some weaponry
                for actor in actorsRemaining:
                    earthquakeReasons = ["falling trees", "a mudslide", "a rolling boulder", "a tsunami", "a horde of displaced zombie fried chickens"]
                    reasonToUse = random.choice(earthquakeReasons)
                    #lose more knives because knives stronger
                    percentageToLose = round(50 - (actor.stats[2]/10 + actor.stats[1]/10), 4)
                    knifePercentageToLose = round(75 - (actor.stats[2]/10 + actor.stats[1]/10), 4)
                    healthToLose = float(random.randint(20, 70)/10.0)
                    healthToLose = round(healthToLose - (actor.stats[0]/100), 4)
                    if healthToLose < 0:
                        healthToLose = 0
                    actor.currentGameHealth -= healthToLose
                    response = actor.displayName + " took " + str(healthToLose) + " damage due to " + reasonToUse + ". \n"
                    knifeToLose = int(knifePercentageToLose/100 * actor.currentGameWeapons[0])
                    arrowToLose = int(percentageToLose/100 * actor.currentGameWeapons[1])
                    bulletToLose = int(percentageToLose/100 * actor.currentGameWeapons[2])
                    actor.currentGameWeapons[0] -= knifeToLose
                    actor.currentGameWeapons[1] -= arrowToLose
                    actor.currentGameWeapons[2] -= bulletToLose
                    response += actor.displayName + " lost " + str(knifeToLose) + " knives, " + str(arrowToLose) + " arrows, and " + str(bulletToLose) + " bullets in the shaking. "
                    actor.currentGameHealth = round(actor.currentGameHealth, 4)
                    if actor.currentGameHealth <= 0:
                        actor.die(None, currentGame)
                        response += "\n" + actor.displayName + " was killed by " + reasonToUse + ". "
                    await ctx.send(response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(2)
                i = 0
                #remove the now dead players
                while i < len(actorsRemaining):
                    if actorsRemaining[i].currentGameHealth <= 0:
                        actorsRemaining.remove(actorsRemaining[i])
                        i -= 1
                    i += 1
                if currentGame.dayOfGame == 2: #update percentage of arena closed - it can only open 10% because arena is only closed 10% on day 2
                    percentage = 10
                elif currentGame.dayOfGame == 1:
                    percentage = 5
                else:
                    percentage = 15
                await ctx.send("Tectonic plates resurface as the ground heaves and pulls apart, expanding the Arena by " + str(percentage) + "%! ")
                writeToFile(currentGame.fileName, "Tectonic plates resurface as the ground heaves and pulls apart, expanding the Arena by " + str(percentage) + "%! ")
                await asyncio.sleep(3)
            elif eventToChoose < gasProbability + 1 + toEach * 2:
                currentGame.currentArenaEvent = 2
                response = "**ARENA EVENT:** A plague of rabid beavers descend upon the arena. "
            elif eventToChoose < gasProbability + 1 + toEach * 3:
                currentGame.currentArenaEvent = 3
                response = "**ARENA EVENT:** FLASH FLOOD! "
                floodFoods = ["fish and chips without the chips", "algae", "seaweed", "wet dried instant noodles", "tasty plankton"]
                floodVerbs = ["trips", "runs into", "falls on", "kicks", "sneezes on", "bites", "fries", "swims into", "splashes"]
            elif currentGame.dayOfGame <= 24: #wolves!
                currentGame.currentArenaEvent = 4
                if currentGame.dayOfGame > 20:
                    animal = "wolf"
                else:
                    animal = "wolves"
                #spawn by 5 - (day/5) in order to scale with number of players left. After day 25, this event is not possible
                wolvesToSpawn = 5 - int(currentGame.dayOfGame/5)
                if wolvesToSpawn > 0:
                    response = "**ARENA EVENT:** Loud howls are heard in the distance. This can only mean one thing. Giant " + animal + " have come to feed. \n"
                    response += str(wolvesToSpawn) + " giant wolves have spawned in the arena!"
                    for i in range(wolvesToSpawn):
                        toSpawn = Player("Giant Wolf")
                        toSpawn.startingHealth = STARTING_HEALTH
                        toSpawn.startingDamage = STARTING_DAMAGE
                        toSpawn.currentGameHealth = STARTING_HEALTH
                        toSpawn.currentGameDamage = STARTING_DAMAGE
                        toSpawn.currentGameAlive = True
                        toSpawn.currentGameWeapons = [0, 0, 0]
                        toSpawn.currentGameKills = 0
                        toSpawn.animalStatus = True
                        toSpawn.changeStats(0, 0, 0)
                        toSpawn.changeCloneStats(0, 0, 0)
                        actorsRemaining.append(toSpawn)
                        currentGame.allPlayers.append(toSpawn)
                        currentGame.playersLeft += 1
                        #increase all dead player's placing by 1 because of new actor
                        for m in range(len(currentGame.allPlayers)):
                            if not currentGame.allPlayers[m].currentGameAlive:
                                currentGame.allPlayers[m].currentGamePlace += 1
                    random.shuffle(actorsRemaining) #shuffle so when choosing actors the wolves aren't all stuck at the beginning
            currentGame.arenaEvents[currentGame.currentArenaEvent] += 1 #update amount of arena events that have happened this game
            if currentGame.currentArenaEvent != 1: #earthquake has it's own special text. all other arena events need to print
                await ctx.send(response)
                writeToFile(currentGame.fileName, response)
                await asyncio.sleep(3)
            response2 = "_ _"
            await ctx.send(response2)
        else:
            currentGame.currentArenaEvent = -1
        #divide the actors remaining into groups of 1 and 2, randomly
        finalActors = []
        i = 0
        while i < len(actorsRemaining):
            tempActors = []
            maxCap = len(actorsRemaining) - i
            if maxCap == 0: #no actors left
                break
            if maxCap > 2:
                maxCap = 2
            if (calcArenaClosure(currentGame, factor = 1, limit = False)) < 20: #before day 20, it's 50/50 whether new group is a group of 1 or group of 2
                toChoose = 50
            else:
                toChoose = 50 - ((calcArenaClosure(currentGame, factor = 1, limit = False)) - 20) * 5 #after day 20, it's 50 - (day - 20) * 5 chance to go into group of 1 (promotes more fighting in the end game)
            if currentGame.currentArenaEvent == 0: #if it's fight to death, only 10% chance to escape without fighting
                toChoose = 10
            randomNumber = random.randint(1, 100)
            if randomNumber < toChoose:
                randomNumber = 1
            else:
                randomNumber = 2
            if randomNumber > maxCap:
                randomNumber = maxCap
            player1Weapons = 40 #random giant number
            player2Weapons = 40
            if randomNumber == 2:
                player1Weapons = actorsRemaining[i].currentGameWeapons[0] + actorsRemaining[i].currentGameWeapons[1] + actorsRemaining[i].currentGameWeapons[2]
                player2Weapons = actorsRemaining[i + 1].currentGameWeapons[0] + actorsRemaining[i + 1].currentGameWeapons[1] + actorsRemaining[i + 1].currentGameWeapons[2]
            if (currentGame.currentArenaEvent == 3 and (player1Weapons < 4 and player2Weapons < 4)) and randomNumber == 2: #if in a two person group, it's flooded, and the two have no weapons, they get split into single groups
                #this prevents weapon stealing, only a feature of flood day, from happening if they have no weapons
                tempActors.append(actorsRemaining[i])
                i += 1
                finalActors.append(tempActors)
                tempActors = []
                tempActors.append(actorsRemaining[i])
                i += 1
            else:
                for j in range(randomNumber):
                    tempActors.append(actorsRemaining[i])
                    i += 1
            if tempActors != []:
                finalActors.append(tempActors)
        count = 0
        for i in range(len(finalActors)):
            for j in range(len(finalActors[i])):
                count += 1
        #for each group, roll a number for each person, the decide what happens based on the roll
        for i in range(len(finalActors)):
            #select text stuff here
            verbToUse = random.choice(verbs)
            if currentGame.currentArenaEvent == 3:
                verbToUse = random.choice(floodVerbs)
            foodToUse = random.choice(foods)
            if currentGame.currentArenaEvent == 3:
                foodToUse = random.choice(floodFoods)
            surpriseToUse = random.choice(surprises)
            peopleInGroup = len(finalActors[i])
    #Singles: fall in random traps, find weapons, heal. Luckiness helps.
    #Doubles: Fight (to the death or 3-8 rounds), make alliance, do same as singles, luckiness = more probability for alliance
    #Triples: Same as 2, battles 2v1 or 1v1v1
    #4s: Same as 2, battles 3v1, 2v2, 2v1v1, or 1v1v1v1
            numbers = []
            for j in range(len(finalActors[i])):
                number = random.randint(1, 100)
                number = number + (finalActors[i][j].stats[2] / 12.0)
                numbers.append(number)
            if peopleInGroup == 1: #one person group
                print(numbers)
                #calculate the prize they found and how many of it here
                prize, weaponPrize, amount, healingAmount = determinePrize(finalActors[i][0], foodToUse)
                #decide if the person will be cloning instead
                toClone = random.randint(1, 100)
                toClone += int(finalActors[i][0].stats[2]/100.0) #luckiness stat factors in
                cloning = True
                #checks if rolled high enough, has the health, and actually wants to clone.
                if toClone < 65: #35% chance to clone if no luckiness
                    cloning = False
                if finalActors[i][0].currentGameHealth <= finalActors[i][0].cloneStats[0]:
                    cloning = False
                if finalActors[i][0].cloneStats[1] <= 0:
                    cloning = False
                if finalActors[i][0].name == "Giant Wolf": #giant wolves cannot pick up weaponry, so always make them take damage from traps and gaining no weaponry.
                    numbers[0] = -100
                if currentGame.currentArenaEvent == 0 and finalActors[i][0].name != "Giant Wolf": #group of 1 in fight to death gas arena event
                    response = finalActors[i][0].displayName + " manages to quickly fashion a mask for themselves before they inhale enough of the gas. They then hide, and escape from the bloodshed. "
                    await ctx.send(response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(4)
                    response2 = "_ _"
                    await ctx.send(response2)
                elif cloning: #if they're cloning, create the clone. exempt from other single player stuff
                    newClone = Player(finalActors[i][0].displayName)
                    response = newClone.becomeClone(finalActors[i][0], finalActors[i][0].cloneStats[1], finalActors[i][0].cloneStats[2])
                    currentGame.allPlayers.append(newClone)
                    await ctx.send(response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(4)
                    response2 = "_ _"
                    await ctx.send(response2)
                    currentGame.playersLeft += 1
                    #increment all dead player's placing by 1
                    for m in range(len(currentGame.allPlayers)):
                        if not currentGame.allPlayers[m].currentGameAlive:
                            currentGame.allPlayers[m].currentGamePlace += 1
                elif numbers[0] <= 40 or (currentGame.currentArenaEvent == 2 and numbers[0] <= 60) or (currentGame.currentArenaEvent == 3 and numbers[0] <= 50): #a trap, more likely during beaver and flood days
                    #no weapon picking up here
                    #calculate damage
                    finalDamage = round(random.randint(100, 300)/100, 4)
                    if currentGame.currentArenaEvent == 2: #rabid beavers do a ton of damage
                        finalDamage *= 3
                        finalDamage = round(finalDamage, 4)
                    #following code makes it so you can't die to single player traps. Removed in an update 3/28/20
#                    if finalActors[i][0].currentGameHealth - finalDamage <= 0:
#                        finalDamage = finalActors[i][0].currentGameHealth - 1.0
#                    if finalDamage < 0:
#                        finalDamage = 0
                    response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, it disappears, and they are left staring at a " + str(surpriseToUse[0]) + ". \n"
                    if currentGame.currentArenaEvent == 2: #beaver
                        response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, it disappears. They realize that they've fallen into a trap set by the rabid beavers. \n"
                        response += "The rabid beavers hiss and lunge at them, sinking their front teeth into their leg, dealing " + str(finalDamage) + " damage. \n"
                    elif currentGame.currentArenaEvent == 3: #flood
                        response = finalActors[i][0].displayName + " finds what looks to be " + prize + " just under the surface of the water. However, as they reach for it, it disappears. \n"
                        response += "A manatee, floating near the surface, mistook " + finalActors[i][0].displayName + "'s hand for a clump of tasty turtle grass and nibbles on it, dealing " + str(finalDamage) + " damage. \n"
                    elif finalDamage > 0: #outdated code that's still here just in case finalDamage somehow is less than 0
                        response += "The " + str(surpriseToUse[0]) + " " + str(surpriseToUse[1])
                        if surpriseToUse[0] != "zombie fried-chicken": #special case for chicken because of grammar
                            response += " on their hand"
                        response += ", dealing " + str(finalDamage) + " damage. \n"
                    else:
                        if currentGame.currentArenaEvent == 2: #beaver
                            response += "They manage to wriggle around and escape just in time as the beaver lunges at their leg. \n"
                        elif currentGame.currentArenaEvent == 3: #flood
                            response += "The manatee realizes its mistake and stops nibbling. \n"
                        else:
                            response += "They pull their hand out just in time as the " + str(surpriseToUse[0]) + " "
                            if surpriseToUse[0] == "zombie fried-chicken":
                                response += "lunges at you with a surgical knife. \n"
                            else:
                                response += str(surpriseToUse[1]) + ". \n"
                    #take the damage
                    finalActors[i][0].currentGameHealth -= finalDamage
                    finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                    response += finalActors[i][0].displayName + " is at " + str(finalActors[i][0].currentGameHealth) + " Health. "
                    #if the poor guy died
                    if finalActors[i][0].currentGameHealth <= 0:
                        finalActors[i][0].die(None, currentGame)
                        animal = str(surpriseToUse[0])
                        if currentGame.currentArenaEvent == 2: #beaver
                            animal = "rabid beaver"
                        elif currentGame.currentArenaEvent == 3: #flood
                            animal = "manatee"
                        response += "\n " + finalActors[i][0].displayName + " was killed by a " + animal + ". Their weaponry was stolen by the " + animal + ". "
                        if currentGame.currentArenaEvent == 3: #flood, easter egg XD
                            response += "The manatee would like to extend its sincerest apologies to " + finalActors[i][0].displayName + ". "
                    if finalActors[i][0].name == "Giant Wolf": #special text set for giant wolf
                        if currentGame.currentArenaEvent == 2: #beaver
                            response = finalActors[i][0].displayName + " realizes that they've fallen into a trap set by the rabid beavers. \n"
                            response += "The rabid beavers hiss and lunge at them, sinking their front teeth into their leg, dealing " + str(finalDamage) + " damage. \n"
                        elif currentGame.currentArenaEvent == 3: #flood
                            response = finalActors[i][0].displayName + " goes to quench its thirst in the water. \n"
                            response += "A manatee, floating near the surface, mistook " + finalActors[i][0].displayName + "'s snout for a clump of tasty turtle grass and nibbles on it, dealing " + str(finalDamage) + " damage. \n"
                        else:
                            response = finalActors[i][0].displayName + " encounters a " + str(surpriseToUse[0]) + ". \n"
                            response += "The " + str(surpriseToUse[0]) + " " + str(surpriseToUse[1])
                            if surpriseToUse[0] != "zombie fried-chicken":
                                response += " on their paw"
                            response += ", dealing " + str(finalDamage) + " damage. \n"
                    await ctx.send("\n\n" + response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(4)
                    response2 = "_ _"
                    await ctx.send(response2)
                elif numbers[0] <= 80 or (currentGame.currentArenaEvent == 2 and numbers[0] <= 100) or (currentGame.currentArenaEvent == 3 and numbers[0] <= 80): #thorn bush, they find weapon but take damage
                    #calculate damage
                    finalDamage = round(random.randint(100, 200)/100, 4)
                    if currentGame.currentArenaEvent == 2:
                        finalDamage *= 3
                        finalDamage = round(finalDamage, 4)
#                    if finalActors[i][0].currentGameHealth - finalDamage <= 0: #for being unable to die to traps
#                        finalDamage = finalActors[i][0].currentGameHealth - 1.0
#                    if finalDamage < 0:
#                        finalDamage = 0
                    response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, they suddenly also notice a " + str(surpriseToUse[0]) + ". \n"
                    if currentGame.currentArenaEvent == 2: #beaver
                        response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, they suddenly realize the pieces of wood up above set up by the rabid beavers. \n"
                        response += "The wood falls, and the rabid beaver leaps on top of them and sinks it's teeth into their hand, dealing " + str(finalDamage) + " damage. They keep the prize. \n"
                    elif currentGame.currentArenaEvent == 3: #flood
                        response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, they suddenly notice a suspicious amount of jellyfish floating nearby. \n"
                        response += finalActors[i][0].displayName + " tries to maneuver carefully, but is stung by one of the jellyfish, taking " + str(finalDamage) + " damage. They keep the prize. \n"
                    elif finalDamage > 0:
                        response += "The " + str(surpriseToUse[0]) + " " + str(surpriseToUse[1])
                        if surpriseToUse[0] != "zombie fried-chicken":
                            response += " on their hand"
                        response += ", dealing " + str(finalDamage) + " damage. They keep the prize. \n"
                    else:
                        if currentGame.currentArenaEvent == 2: #beaver
                            response += "They manage to wriggle around and escape just in time as the beaver lunges at their leg. \n"
                        elif currentGame.currentArenaEvent == 3: #flood
                            response += "They successfully maneuver their way around the jellyfish tentacles. \n"
                        else:
                            response += "They pull out their hand, and the prize, just in time as the " + str(surpriseToUse[0]) + " "
                            if surpriseToUse[0] != "zombie fried-chicken":
                                response += str(surpriseToUse[1]) + ". \n"
                            else:
                                response += "lunges at you with a surgical knife. \n"
                    finalActors[i][0].currentGameHealth -= finalDamage
                    finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                    #weapon giving out
                    if weaponPrize == "knife":
                        finalActors[i][0].currentGameWeapons[0] += 1
                        response += finalActors[i][0].displayName + " acquired a knife! "
                    elif weaponPrize == "bow":
                        finalActors[i][0].currentGameWeapons[1] += amount
                        response += finalActors[i][0].displayName + " acquired " + str(amount) + " arrows! "
                    elif weaponPrize == "gun":
                        finalActors[i][0].currentGameWeapons[2] += amount
                        response += finalActors[i][0].displayName + " acquired " + str(amount) + " bullets! "
                    else:
                        finalActors[i][0].currentGameHealth += healingAmount
                        finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                        response += finalActors[i][0].displayName + " gained " + str(healingAmount) + " Health! "
                    response += finalActors[i][0].displayName + " is at " + str(finalActors[i][0].currentGameHealth) + " Health. "
                    #oof they died
                    if finalActors[i][0].currentGameHealth <= 0:
                        finalActors[i][0].die(None, currentGame)
                        animal = str(surpriseToUse[0])
                        if currentGame.currentArenaEvent == 2: #beaver
                            animal = "rabid beaver"
                        elif currentGame.currentArenaEvent == 3: #flood
                            animal = "jellyfish"
                        response += "\n " + finalActors[i][0].displayName + " was killed by a " + animal + ". Their weaponry was stolen by the " + animal + ". "
                    await ctx.send("\n\n" + response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(4)
                    response2 = "_ _"
                    await ctx.send(response2)
                elif numbers[0] <= 100 or (currentGame.currentArenaEvent == 2 and numbers[0] <= 120) or (currentGame.currentArenaEvent == 3 and numbers[0] <= 120): #in the open, no damage taken
                    response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, they suddenly also notice a " + str(surpriseToUse[0]) + ". \n"
                    response += "They pull out their hand, and the prize, just in time as the " + str(surpriseToUse[0]) + " " + str(surpriseToUse[1]) + ". \n"
                    if currentGame.currentArenaEvent == 2: #beaver
                        response = finalActors[i][0].displayName + " finds what looks to be " + prize + ". However, as they reach for it, they suddenly also notice the wood arch they stepped into... and the gleaming eyes of a rabid beaver. \n"
                        response += "They pull out their hand, and the prize, just in time as the rabid beaver leaps down and tries to bite their leg. \n"
                    elif currentGame.currentArenaEvent == 3: #flood
                        response = finalActors[i][0].displayName + " goes fishing. After a few hours without luck, they reel in their line and find " + prize + " attached to it. \n"
                    #deal out weapons
                    if weaponPrize == "knife":
                        finalActors[i][0].currentGameWeapons[0] += 1
                        response += finalActors[i][0].displayName + " acquired a knife! "
                    elif weaponPrize == "bow":
                        finalActors[i][0].currentGameWeapons[1] += amount
                        response += finalActors[i][0].displayName + " acquired " + str(amount) + " arrows! "
                    elif weaponPrize == "gun":
                        finalActors[i][0].currentGameWeapons[2] += amount
                        response += finalActors[i][0].displayName + " acquired " + str(amount) + " bullets! "
                    else:
                        finalActors[i][0].currentGameHealth += healingAmount
                        finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                        response += finalActors[i][0].displayName + " gained " + str(healingAmount) + " Health! "
                    response += finalActors[i][0].displayName + " is at " + str(finalActors[i][0].currentGameHealth) + " Health. "
                    await ctx.send("\n\n" + response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(4)
                    response2 = "_ _"
                    await ctx.send(response2)
                else: #find 2x prize
                    prize2, weaponPrize2, amount2, healingAmount2 = determinePrize(finalActors[i][0], foodToUse)
                    response = finalActors[i][0].displayName + " stumbles upon " + prize + " and " + prize2 + " in an open field! How lucky! \n"
                    if currentGame.currentArenaEvent == 3: #flood
                        response = finalActors[i][0].displayName + " was out fishing. As they reel their line in, they find " + prize + " and " + prize2 + " attached to their hook! How lucky! \n"
                    #deal out weapon prize 1
                    if weaponPrize == "knife":
                        finalActors[i][0].currentGameWeapons[0] += 1
                        response += finalActors[i][0].displayName + " acquired a knife! "
                    elif weaponPrize == "bow":
                        finalActors[i][0].currentGameWeapons[1] += amount
                        response += finalActors[i][0].displayName + " acquired " + str(amount) + " arrows! "
                    elif weaponPrize == "gun":
                        finalActors[i][0].currentGameWeapons[2] += amount
                        response += finalActors[i][0].displayName + " acquired " + str(amount) + " bullets! "
                    else:
                        finalActors[i][0].currentGameHealth += healingAmount
                        finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                        response += finalActors[i][0].displayName + " gained " + str(healingAmount) + " Health! "
                    #deal out weapon prize 2
                    if weaponPrize2 == "knife":
                        finalActors[i][0].currentGameWeapons[0] += 1
                        response += finalActors[i][0].displayName + " acquired a knife! "
                    elif weaponPrize2 == "bow":
                        finalActors[i][0].currentGameWeapons[1] += amount2
                        response += finalActors[i][0].displayName + " acquired " + str(amount2) + " arrows! "
                    elif weaponPrize2 == "gun":
                        finalActors[i][0].currentGameWeapons[2] += amount2
                        response += finalActors[i][0].displayName + " acquired " + str(amount2) + " bullets! "
                    else:
                        finalActors[i][0].currentGameHealth += healingAmount2
                        finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                        response += finalActors[i][0].displayName + " gained " + str(healingAmount2) + " Health! "
                    response += finalActors[i][0].displayName + " is at " + str(finalActors[i][0].currentGameHealth) + " Health. "
                    await ctx.send("\n\n" + response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(4)
                    response2 = "_ _"
                    await ctx.send(response2)
            if peopleInGroup == 2: #group of 2
                print("In group of 2")
                print(numbers)
                #test to make sure the two aren't related by cloning. Uses while loops in case it's grandparents or smthg
                isParent = False
                testParent = finalActors[i][0]
                while testParent.currentGameParent != None and not isParent:
                    if testParent.currentGameParent == finalActors[i][1]:
                        isParent = True
                    testParent = testParent.currentGameParent
                testParent = finalActors[i][1]
                while testParent.currentGameParent != None and not isParent:
                    if testParent.currentGameParent == finalActors[i][0]:
                        isParent = True
                    testParent = testParent.currentGameParent
                if finalActors[i][0].currentGameParent == finalActors[i][1].currentGameParent and finalActors[i][0].currentGameParent != None:
                    isParent = True
                if currentGame.currentArenaEvent == 0: #fight to the death gas, forces everyone to fight to death
                    numbers = [-100, -100]
                if finalActors[i][0].name == "Giant Wolf": #always fights
                    numbers[0] = -100
                if finalActors[i][1].name == "Giant Wolf": #always fights
                    numbers[1] = -100
                if numbers[0] < (calcArenaClosure(currentGame, factor = 5, limit = False)) and currentGame.currentArenaEvent == 3: #on flood day, set it so they can't fight
                    if (calcArenaClosure(currentGame, factor = 5, limit = False)) < 100: 
                        number = random.randint((calcArenaClosure(currentGame, factor = 5, limit = False)), 100)
                    else:
                        number = 101
                    number = number + (finalActors[i][j].stats[2] / 12.0)
                    numbers[0] = number
                if numbers[1] < (calcArenaClosure(currentGame, factor = 5, limit = False)) and currentGame.currentArenaEvent == 3: #on flood day, set it so they can't fight
                    if (calcArenaClosure(currentGame, factor = 5, limit = False)) < 100:
                        number = random.randint((calcArenaClosure(currentGame, factor = 5, limit = False)), 100)
                    else:
                        number = 101
                    number = number + (finalActors[i][j].stats[2] / 12.0)
                    numbers[1] = number
                if numbers[0] < (calcArenaClosure(currentGame, factor = 3, limit = False)) and numbers[1] < (calcArenaClosure(currentGame, factor = 3, limit = False)): #fight to the death
                    if isParent and currentGame.currentArenaEvent != 0: #they're related, so no fighting
                        await ctx.send(finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " were going to fight to the death, but then they realized they're related. They leave in peace. ")
                        writeToFile(currentGame.fileName, finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " were going to fight to the death, but then they realized they're related. They leave in peace. ")
                        await asyncio.sleep(3)
                        await ctx.send("_ _")
                    else:
                        if isParent: #this is only printed during gas and they're related
                            response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " know they are related. But the gas compels them. "
                            await ctx.send(response)
                            writeToFile(currentGame.fileName, response)
                        responses = battle(finalActors[i], verbToUse, currentGame, rounds = -1)
                        for response4 in responses:
                            await ctx.send(response4)
                            if response4 != "_ _":
                                writeToFile(currentGame.fileName, response4)
                            await asyncio.sleep(3)
                elif numbers[0] < (calcArenaClosure(currentGame, factor = 5, limit = False)) and numbers[1] < (calcArenaClosure(currentGame, factor = 5, limit = False)): #fight 3-8 rounds
                    if isParent: #they're related, so no fighting
                        await ctx.send(finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " were going to fight, but then they realized they're related. They leave in peace. ")
                        writeToFile(currentGame.fileName, finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " were going to fight, but then they realized they're related. They leave in peace. ")
                        await asyncio.sleep(3)
                        await ctx.send("_ _")
                    else:
                        rounds = random.randint(3, 8)
                        responses = battle(finalActors[i], verbToUse, currentGame, rounds = rounds)
                        for response4 in responses:
                            await ctx.send(response4)
                            if response4 != "_ _":
                                writeToFile(currentGame.fileName, response4)
                            await asyncio.sleep(3)
                elif numbers[0] < (calcArenaClosure(currentGame, factor = 5, limit = False)) and numbers[1] >= (calcArenaClosure(currentGame, factor = 5, limit = False)): #player 1 attacks player 2, player 2 gets weapon/medkit (one weapon/medkit only)
                    #determine prize
                    prize, weaponPrize, amount, healingAmount = determinePrize(finalActors[i][1], foodToUse)
                    response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " stumble upon " + prize + ". \n"
                    if currentGame.currentArenaEvent == 2: #beaver
                        response = "While running from rabid beavers, " + finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " stumble upon " + prize + ". \n"
                    #calc damage
                    finalDamage = finalActors[i][0].currentGameDamage
                    theirWeapon = "their fist"
                    if finalActors[i][0].currentGameWeapons[0] > 0: #different formula here, lower numbers to reduce instances of dying by attrition in the end game
                        if finalActors[i][0].currentGameWeapons[0] <= 16: #point of interception: (16.942, 3.041)
                            finalDamage = finalDamage * round((0.5 + 0.15 * finalActors[i][0].currentGameWeapons[0]), 4)
                        else:
                            finalDamage = finalDamage * round(math.log(finalActors[i][0].currentGameWeapons[0]), 4)
                        theirWeapon = "their knife"
                    if finalActors[i][0].currentGameWeapons[1] > 0 and finalActors[i][0].currentGameWeapons[0] < 7:
                        finalDamage = finalDamage * 1.3125
                        theirWeapon = "one of their arrows"
                    if finalActors[i][0].currentGameWeapons[2] > 0 and finalActors[i][0].currentGameWeapons[0] < 11:
                        finalDamage = finalDamage * 1.75
                        theirWeapon = "one of their bullets"
                    if finalActors[i][0].name == "Giant Wolf":
                        theirWeapon = "their sharp claws"
                    #kill streak factored in
                    factor = float((finalActors[i][0].currentGameKills - 1)/2)
                    if factor < 1:
                        factor = 1
                    finalDamage *= factor
                    finalDamage = round(finalDamage, 4)
                    if currentGame.currentArenaEvent == 3: #flood, so special case
                        if finalDamage == 0:
                            response = finalActors[i][1].displayName + " is walking through the flooded forest when they see " + finalActors[i][0].displayName + " sitting in a tree to hide from the water. They quickly duck for cover and escape. \n"
                        elif finalDamage > finalActors[i][1].currentGameHealth:
                            response = finalActors[i][1].displayName + " is walking through the flooded forest when they see " + finalActors[i][0].displayName + " sitting in a tree to hide from the water. Before they can escape, " + finalActors[i][0].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][1].displayName + ", killing " + finalActors[i][1].displayName + ". \n"
                        else:
                            response = finalActors[i][1].displayName + " is walking through the flooded forest when they see " + finalActors[i][0].displayName + " sitting in a tree to hide from the water. Before they can escape, " + finalActors[i][0].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][1].displayName + ". \n"
                    elif currentGame.currentArenaEvent == 2: #beaver
                        if finalDamage == 0:
                            response += finalActors[i][1].displayName + " stops to grab the prize, then sprints to rejoin " + finalActors[i][0].displayName + ", and they both run away before the beavers catch up. \n"
                        elif finalDamage > finalActors[i][1].currentGameHealth:
                            response += finalActors[i][1].displayName + " stops to grab the prize, but the beavers catch up, dealing " + str(finalDamage) + " damage to " + finalActors[i][1].displayName + " and killing " + finalActors[i][1].displayName + " before they could make use of it. \nThe prize is lost somewhere in the mud. " + finalActors[i][0].displayName + " gets away. \n"
                        else:
                            response += finalActors[i][1].displayName + " stops to grab the prize, but the beavers catch up, dealing " + str(finalDamage) + " damage to " + finalActors[i][1].displayName + " as they run to rejoin " + finalActors[i][0].displayName + ". \n"
                    elif isParent: #it's a relative, so no need to damage
                        response += finalActors[i][1].displayName + " grabs the prize first. " + finalActors[i][0].displayName + " was going to fight, but then they realized the two of them are related. They leave in peace. \n"
                    elif finalDamage == 0:
                        response += finalActors[i][1].displayName + " grabs the prize first. " + finalActors[i][0].displayName + " misses with " + theirWeapon + " as they run away. \n"
                    elif finalDamage > finalActors[i][1].currentGameHealth: #killed by the damage
                        response += finalActors[i][1].displayName + " grabs the prize first, but " + finalActors[i][0].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][1].displayName + ", killing " + finalActors[i][1].displayName + " before they could make use of it. \nThe prize is lost somewhere in the mud. \n"
                    else:
                        response += finalActors[i][1].displayName + " grabs the prize first. " + finalActors[i][0].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][1].displayName + " as they run away. \n"
                    #update all values
                    if not isParent:
                        finalActors[i][1].currentGameHealth -= finalDamage
                        finalActors[i][1].currentGameHealth = round(finalActors[i][1].currentGameHealth, 4)
                        if currentGame.currentArenaEvent != 2:
                            if finalActors[i][0].currentGameWeapons[2] > 0 and finalActors[i][0].currentGameWeapons[0] < 11:
                                finalActors[i][0].currentGameWeapons[2] -= 1
                            elif finalActors[i][0].currentGameWeapons[1] > 0 and finalActors[i][0].currentGameWeapons[0] < 7:
                                finalActors[i][0].currentGameWeapons[1] -= 1
                    if finalActors[i][1].currentGameHealth <= 0:
                        if currentGame.currentArenaEvent == 2: #beaver
                            finalActors[i][1].die(None, currentGame)
                            response += "\n " + finalActors[i][1].displayName + " was killed by rabid beavers, who then stole all the weaponry. "
                        else:
                            response += finalActors[i][1].die(finalActors[i][0], currentGame)
                    elif currentGame.currentArenaEvent != 3: #not flood day - on flood days no weapons are found, it's just tree sniping
                        if weaponPrize == "knife":
                            finalActors[i][1].currentGameWeapons[0] += 1
                            response += finalActors[i][1].displayName + " acquired a knife! "
                        elif weaponPrize == "bow":
                            finalActors[i][1].currentGameWeapons[1] += amount
                            response += finalActors[i][1].displayName + " acquired " + str(amount) + " arrows! "
                        elif weaponPrize == "gun":
                            finalActors[i][1].currentGameWeapons[2] += amount
                            response += finalActors[i][1].displayName + " acquired " + str(amount) + " bullets! "
                        else:
                            finalActors[i][1].currentGameHealth += healingAmount
                            finalActors[i][1].currentGameHealth = round(finalActors[i][1].currentGameHealth, 4)
                            response += finalActors[i][1].displayName + " gained " + str(healingAmount) + " Health! "
                    response += finalActors[i][1].displayName + " is at " + str(finalActors[i][1].currentGameHealth) + " Health. "
                    await ctx.send("\n\n" + response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(3)
                    response2 = "_ _"
                    await ctx.send(response2)
                elif numbers[0] >= (calcArenaClosure(currentGame, factor = 5, limit = False)) and numbers[1] < (calcArenaClosure(currentGame, factor = 5, limit = False)): #player 2 attacks player 1, player 1 gets weapon/medkit (one weapon/medkit only)
                    #det prize
                    prize, weaponPrize, amount, healingAmount = determinePrize(finalActors[i][0], foodToUse)
                    response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " stumble upon " + prize + ". \n"
                    if currentGame.currentArenaEvent == 2:
                        response = "While running from rabid beavers, " + finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " stumble upon " + prize + ". \n"
                    damage = finalActors[i][1].currentGameDamage
                    finalDamage = damage
                    theirWeapon = "their fist"
                    if finalActors[i][1].currentGameWeapons[0] > 0:
                        if finalActors[i][1].currentGameWeapons[0] <= 16: #point of interception: (16.942, 3.041)
                            finalDamage = damage * round((0.5 + 0.15 * finalActors[i][1].currentGameWeapons[0]), 4)
                        else:
                            finalDamage = damage * round(math.log(finalActors[i][1].currentGameWeapons[0]), 4)
                        theirWeapon = "their knife"
                    if finalActors[i][1].currentGameWeapons[1] > 0 and finalActors[i][1].currentGameWeapons[0] < 7:
                        finalDamage = damage * 1.3125
                        theirWeapon = "one of their arrows"
                    if finalActors[i][1].currentGameWeapons[2] > 0 and finalActors[i][1].currentGameWeapons[0] < 11:
                        finalDamage = damage * 1.75
                        theirWeapon = "one of their bullets"
                    if finalActors[i][1].name == "Giant Wolf":
                        theirWeapon = "their sharp claws"
                    factor = float((finalActors[i][1].currentGameKills - 1)/2)
                    if factor <= 1:
                        factor = 1
                    finalDamage *= factor
                    finalDamage = round(finalDamage, 4)
                    if currentGame.currentArenaEvent == 3:
                        if finalDamage == 0:
                            response = finalActors[i][0].displayName + " is walking through the flooded forest when they see " + finalActors[i][1].displayName + " fishing in the floodwaters. They quickly duck for cover and escape. \n"
                        elif finalDamage > finalActors[i][0].currentGameHealth:
                            response = finalActors[i][0].displayName + " is walking through the flooded forest when they see " + finalActors[i][1].displayName + " fishing in the floodwaters. Before they can escape, " + finalActors[i][1].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][0].displayName + ", killing " + finalActors[i][0].displayName + ". \n"
                        else:
                            response = finalActors[i][0].displayName + " is walking through the flooded forest when they see " + finalActors[i][1].displayName + " fishing in the floodwaters. Before they can escape, " + finalActors[i][1].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][0].displayName + ". \n"
                    elif currentGame.currentArenaEvent == 2:
                        if finalDamage == 0:
                            response += finalActors[i][0].displayName + " stops to grab the prize, then sprints to rejoin " + finalActors[i][1].displayName + ", and they both run away before the beavers catch up. \n"
                        elif finalDamage > finalActors[i][0].currentGameHealth:
                            response += finalActors[i][0].displayName + " stops to grab the prize, but the beavers catch up, dealing " + str(finalDamage) + " damage to " + finalActors[i][0].displayName + " and killing " + finalActors[i][0].displayName + " before they could make use of it. \nThe prize is lost somewhere in the mud. " + finalActors[i][1].displayName + " gets away. \n"
                        else:
                            response += finalActors[i][0].displayName + " stops to grab the prize, but the beavers catch up, dealing " + str(finalDamage) + " damage to " + finalActors[i][0].displayName + " as they run to rejoin " + finalActors[i][1].displayName + ". \n"
                    elif isParent:
                        response += finalActors[i][0].displayName + " grabs the prize first. " + finalActors[i][1].displayName + " was going to fight, but then they realized the two of them are related. They leave in peace. \n"
                    elif finalDamage == 0:
                        response += finalActors[i][0].displayName + " grabs the prize first. " + finalActors[i][1].displayName + " misses with " + theirWeapon + " as they run away. \n"
                    elif finalDamage > finalActors[i][0].currentGameHealth:
                        response += finalActors[i][0].displayName + " grabs the prize first, but " + finalActors[i][1].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][0].displayName + ", killing " + finalActors[i][0].displayName + " before they could make use of it. \nThe prize is lost somewhere in the mud. "
                    else:
                        response += finalActors[i][0].displayName + " grabs the prize first. " + finalActors[i][1].displayName + " uses " + theirWeapon + " to deal " + str(finalDamage) + " damage to " + finalActors[i][0].displayName + " as they run away. \n"
                    #update all values
                    if not isParent:
                        finalActors[i][0].currentGameHealth -= finalDamage
                        finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                        if currentGame.currentArenaEvent != 2:
                            if finalActors[i][1].currentGameWeapons[2] > 0 and finalActors[i][1].currentGameWeapons[0] < 11:
                                finalActors[i][1].currentGameWeapons[2] -= 1
                            elif finalActors[i][1].currentGameWeapons[1] > 0 and finalActors[i][1].currentGameWeapons[0] < 7:
                                finalActors[i][1].currentGameWeapons[1] -= 1
                    if finalActors[i][0].currentGameHealth <= 0:
                        if currentGame.currentArenaEvent == 2:
                            finalActors[i][0].die(None, currentGame)
                            response += "\n " + finalActors[i][1].displayName + " was killed by rabid beavers, who stole all their weaponry. "
                        else:
                            response += finalActors[i][0].die(finalActors[i][1], currentGame)
                    elif currentGame.currentArenaEvent != 3:
                        if weaponPrize == "knife":
                            finalActors[i][0].currentGameWeapons[0] += 1
                            response += finalActors[i][0].displayName + " acquired a knife! "
                        elif weaponPrize == "bow":
                            finalActors[i][0].currentGameWeapons[1] += amount
                            response += finalActors[i][0].displayName + " acquired " + str(amount) + " arrows! "
                        elif weaponPrize == "gun":
                            finalActors[i][0].currentGameWeapons[2] += amount
                            response += finalActors[i][0].displayName + " acquired " + str(amount) + " bullets! "
                        else:
                            finalActors[i][0].currentGameHealth += healingAmount
                            finalActors[i][0].currentGameHealth = round(finalActors[i][0].currentGameHealth, 4)
                            response += finalActors[i][0].displayName + " gained " + str(healingAmount) + " Health! "
                    response += finalActors[i][0].displayName + " is at " + str(finalActors[i][0].currentGameHealth) + " Health. "
                    await ctx.send("\n\n" + response)
                    writeToFile(currentGame.fileName, response)
                    await asyncio.sleep(3)
                    response2 = "_ _"
                    await ctx.send(response2)
                elif numbers[0] >= (calcArenaClosure(currentGame, factor = 5, limit = False)) and numbers[1] >= (calcArenaClosure(currentGame, factor = 5, limit = False)): #two weapons, both pick up and leave
                    player1Weapons = finalActors[i][0].currentGameWeapons[0] + finalActors[i][0].currentGameWeapons[1] + finalActors[i][0].currentGameWeapons[2]
                    player2Weapons = finalActors[i][1].currentGameWeapons[0] + finalActors[i][1].currentGameWeapons[1] + finalActors[i][1].currentGameWeapons[2]
                    if currentGame.currentArenaEvent != 3 or (player1Weapons < 4 and player2Weapons < 4): #if it's flood day, weapon flow happens here. If it's not flood day or there aren't enough weapons to flow, then two prizes
                        prize, weaponPrize, amount, healingAmount = determinePrize(finalActors[i][0], foodToUse)
                        prize2, weaponPrize2, amount2, healingAmount2 = determinePrize(finalActors[i][1], foodToUse)
                        response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " stumble upon " + prize + " and " + prize2 + ". \n"
                        if currentGame.currentArenaEvent == 2: #beavers
                            response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + ", while running away from rabid beavers, stumble upon " + prize + " and " + prize2 + ". \n"
                        toWhom = random.randint(1, 2)
                        toWhom -= 1
                        if toWhom == 0:
                            other = 1
                        else:
                            other = 0
                        if weaponPrize == "knife":
                            finalActors[i][toWhom].currentGameWeapons[0] += 1
                            response += finalActors[i][toWhom].displayName + " acquired a knife! "
                        elif weaponPrize == "bow":
                            finalActors[i][toWhom].currentGameWeapons[1] += amount
                            response += finalActors[i][toWhom].displayName + " acquired " + str(amount) + " arrows! "
                        elif weaponPrize == "gun":
                            finalActors[i][toWhom].currentGameWeapons[2] += amount
                            response += finalActors[i][toWhom].displayName + " acquired " + str(amount) + " bullets! "
                        else:
                            finalActors[i][toWhom].currentGameHealth += healingAmount
                            finalActors[i][toWhom].currentGameHealth = round(finalActors[i][toWhom].currentGameHealth, 4)
                            response += finalActors[i][toWhom].displayName + " gained " + str(healingAmount) + " Health! "
                        if weaponPrize2 == "knife":
                            finalActors[i][other].currentGameWeapons[0] += 1
                            response += finalActors[i][other].displayName + " acquired a knife! "
                        elif weaponPrize2 == "bow":
                            finalActors[i][other].currentGameWeapons[1] += amount2
                            response += finalActors[i][other].displayName + " acquired " + str(amount2) + " arrows! "
                        elif weaponPrize2 == "gun":
                            finalActors[i][other].currentGameWeapons[2] += amount2
                            response += finalActors[i][other].displayName + " acquired " + str(amount2) + " bullets! "
                        else:
                            finalActors[i][other].currentGameHealth += healingAmount2
                            finalActors[i][other].currentGameHealth = round(finalActors[i][other].currentGameHealth, 4)
                            response += finalActors[i][other].displayName + " gained " + str(healingAmount2) + " Health! "
                        if currentGame.currentArenaEvent == 2: #beavers
                            response += "\nThey then are barely able to get away from the beavers. "
                        await ctx.send("\n\n" + response)
                        writeToFile(currentGame.fileName, response)
                        await asyncio.sleep(3)
                        response2 = "_ _"
                        await ctx.send(response2)
                    else: #weapon flow
                        if player1Weapons < 4: #if one player doesn't have enough weapons, they must be the receiver of the weapon flow
                            index = 1
                        elif player2Weapons < 4:
                            index = 0
                        else:
                            firstNum = 0 #roll until numbers aren't equal
                            secondNum = 0
                            while firstNum == secondNum:
                                firstNum = random.randint(1, 100)
                                firstNum = firstNum + (finalActors[i][0].stats[2] / 12.0)
                                secondNum = random.randint(1, 100)
                                secondNum = secondNum + (finalActors[i][0].stats[2] / 12.0)
                            if firstNum > secondNum: #highroller gets weaponry
                                index = 1
                            else:
                                index = 0
                        if index == 0: #index is the one giving
                            otherIndex = 1
                        else:
                            otherIndex = 0
                        playerWeapons = [player1Weapons, player2Weapons]
                        #losing weaponry first.
                        #Loop through the following: choose a weapon to lose that they have, subract, and repeat until 50% of weaponry gone
                        toLose = [0, 0, 0]
                        weapon = 0
                        toChooseFrom = []
                        knifeCheck = False
                        arrowCheck = False
                        bulletCheck = False
                        if finalActors[i][index].currentGameWeapons[0] > 0:
                            toChooseFrom.append(0)
                            knifeCheck = True
                        if finalActors[i][index].currentGameWeapons[1] > 0:
                            toChooseFrom.append(1)
                            arrowCheck = True
                        if finalActors[i][index].currentGameWeapons[2] > 0:
                            toChooseFrom.append(2)
                            bulletCheck = True
                        while weapon < int(playerWeapons[index]/2):
                            losing = random.randint(1, len(toChooseFrom))
                            toLose[toChooseFrom[losing - 1]] += 1
                            if toLose[0] == finalActors[i][index].currentGameWeapons[0] and 0 in toChooseFrom and knifeCheck:
                                toChooseFrom.remove(0)
                            if toLose[1] == finalActors[i][index].currentGameWeapons[1] and 1 in toChooseFrom and arrowCheck:
                                toChooseFrom.remove(1)
                            if toLose[2] == finalActors[i][index].currentGameWeapons[2] and 2 in toChooseFrom and bulletCheck:
                                toChooseFrom.remove(2)
                            weapon += 1
                        if toLose[0] == 1:
                            knife = "knife"
                        else:
                            knife = "knives"
                        if toLose[1] == 1:
                            arrow = "arrow"
                        else:
                            arrow = "arrows"
                        if toLose[2] == 1:
                            bullet = "bullet"
                        else:
                            bullet = "bullets"
                        response = "Surprised by the sudden influx of water, " + finalActors[i][index].displayName + " is knocked over and drops " + str(toLose[0]) + " " + knife + ", " + str(toLose[1]) + " " + arrow + ", and " + str(toLose[2]) + " " + bullet + ". They are lost in the water. \n"
                        finalActors[i][index].currentGameWeapons[0] -= toLose[0]
                        finalActors[i][index].currentGameWeapons[1] -= toLose[1]
                        finalActors[i][index].currentGameWeapons[2] -= toLose[2]
                        #calculate finding weapons, same algorithm from above, pool is the dropped weapons
                        toFind = [0, 0, 0]
                        weapon = 0
                        toChooseFrom = []
                        if toLose[0] > 0:
                            toChooseFrom.append(0)
                        if toLose[1] > 0:
                            toChooseFrom.append(1)
                        if toLose[2] > 0:
                            toChooseFrom.append(2)
                        while weapon < int(playerWeapons[index]/4):
                            losing = random.randint(1, len(toChooseFrom))
                            toFind[toChooseFrom[losing - 1]] += 1
                            if toFind[0] == toLose[0] and 0 in toChooseFrom:
                                toChooseFrom.remove(0)
                            if toFind[1] == toLose[1] and 1 in toChooseFrom:
                                toChooseFrom.remove(1)
                            if toFind[2] == toLose[2] and 2 in toChooseFrom:
                                toChooseFrom.remove(2)
                            weapon += 1
                        if toFind[0] == 1:
                            knife = "knife"
                        else:
                            knife = "knives"
                        if toFind[1] == 1:
                            arrow = "arrow"
                        else:
                            arrow = "arrows"
                        if toFind[2] == 1:
                            bullet = "bullet"
                        else:
                            bullet = "bullets"
                        if toFind[0] == 0 and toFind[1] == 0 and toFind[2] == 0:
                            response += finalActors[i][otherIndex].displayName + " goes fishing for a few hours but catches nothing. \n"
                        else:
                            response += finalActors[i][otherIndex].displayName + " is splashing around when they notice " + str(toFind[0]) + " " + knife + ", " + str(toFind[1]) + " " + arrow + ", and " + str(toFind[2]) + " " + bullet + " floating around. They look a little worn, as if they had been carried around. Where could they possibly have come from? " + finalActors[i][otherIndex].displayName + " keeps the weaponry they found. \n"
                        finalActors[i][otherIndex].currentGameWeapons[0] += toFind[0]
                        finalActors[i][otherIndex].currentGameWeapons[1] += toFind[1]
                        finalActors[i][otherIndex].currentGameWeapons[2] += toFind[2]
                        print("output")
                        await ctx.send(response)
                        writeToFile(currentGame.fileName, response)
                        await asyncio.sleep(3)
                        response2 = "_ _"
                        await ctx.send(response2)
            if peopleInGroup == 3: #3 person group, impossible to reach for now
                response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " and " + finalActors[i][2].displayName + " settle down for a nice nap. "
                await ctx.send("\n\n" + response)
                writeToFile(currentGame.fileName, response)
                await asyncio.sleep(3)
                response2 = "_ _"
                await ctx.send(response2)
            if peopleInGroup == 4: #4 person group, impossible to reach for now
                response = finalActors[i][0].displayName + " and " + finalActors[i][1].displayName + " and " + finalActors[i][2].displayName + " and " + finalActors[i][3].displayName + " settle down to eat dinner. "
                await ctx.send("\n\n" + response)
                writeToFile(currentGame.fileName, response)
                await asyncio.sleep(3)
                response2 = "_ _"
                await ctx.send(response2)
        #End of day procedures:
        response = ""
        tempResponse = ""
        for i in range(len(finalActors)):
            for j in range(len(finalActors[i])):
                if finalActors[i][j].currentGameParent != None: #for clones, if their parents are not alive, self destruct
                    if not finalActors[i][j].currentGameParent.currentGameAlive:
                        finalActors[i][j].die(None, currentGame)
                        response += "With their parent dead, " + finalActors[i][j].displayName + " self-destructs. \n"
                        if len(response) >= DISCORD_MAX_MESSAGE_LENGTH:
                            await ctx.send(tempResponse)
                            writeToFile(currentGame.fileName, tempResponse)
                            response = "With their parent dead, " + finalActors[i][j].displayName + " self-destructs. \n"
                            tempResponse = ""
                        tempResponse += "With their parent dead, " + finalActors[i][j].displayName + " self-destructs. \n"
                    else: #if clone's parents aren't dead, and they have weaponry, give all the weapons over to parent
                        if (finalActors[i][j].currentGameWeapons[0] != 0 or finalActors[i][j].currentGameWeapons[1] != 0 or finalActors[i][j].currentGameWeapons[2] != 0) and finalActors[i][j].currentGameHealth > 0:
                            response += "At the end of the day, " + str(finalActors[i][j].displayName) + " gives all the weapons they found to " + finalActors[i][j].currentGameParent.displayName + ". \n"
                            finalActors[i][j].currentGameParent.currentGameWeapons[1] += finalActors[i][j].currentGameWeapons[1]
                            finalActors[i][j].currentGameParent.currentGameWeapons[2] += finalActors[i][j].currentGameWeapons[2]
                            finalActors[i][j].currentGameParent.currentGameWeapons[0] += finalActors[i][j].currentGameWeapons[0]
                            finalActors[i][j].currentGameWeapons[0] = 0
                            finalActors[i][j].currentGameWeapons[1] = 0
                            finalActors[i][j].currentGameWeapons[2] = 0
                            if len(response) >= DISCORD_MAX_MESSAGE_LENGTH:
                                await ctx.send(tempResponse)
                                writeToFile(currentGame.fileName, tempResponse)
                                response = "At the end of the day, " + str(finalActors[i][j].displayName) + " gives all the weapons they found to " + finalActors[i][j].currentGameParent.displayName + ". \n"
                                tempResponse = ""
                            tempResponse += "At the end of the day, " + str(finalActors[i][j].displayName) + " gives all the weapons they found to " + finalActors[i][j].currentGameParent.displayName + ". \n"
                        if finalActors[i][j].currentGameHealth > 0: #heal parent
                            response += "During the night, " + str(finalActors[i][j].currentGameParent.displayName) + " is able to get a good night's sleep because of " + finalActors[i][j].displayName + "'s guard. "
                            toGain = 1 + (finalActors[i][j].currentGameParent.stats[0] / 200.0)
                            toGain = round(toGain, 4)
                            response += "Some of " + str(finalActors[i][j].currentGameParent.displayName) + "'s wounds healed, and they gained " + str(toGain) + " Health! \n"
                            finalActors[i][j].currentGameParent.currentGameHealth += toGain
                            finalActors[i][j].currentGameParent.currentGameHealth = round(finalActors[i][j].currentGameParent.currentGameHealth, 4)
                            response += "\n"
                            if len(response) >= DISCORD_MAX_MESSAGE_LENGTH:
                                await ctx.send(tempResponse)
                                writeToFile(currentGame.fileName, tempResponse)
                                response = "During the night, " + str(finalActors[i][j].currentGameParent.displayName) + " is able to get a good night's sleep because of " + finalActors[i][j].displayName + "'s guard. "
                                response += "Some of " + str(finalActors[i][j].currentGameParent.displayName) + "'s wounds healed, and they gained " + str(toGain) + " Health! \n"
                                response += "\n"
                                tempResponse = ""
                            tempResponse += "During the night, " + str(finalActors[i][j].currentGameParent.displayName) + " is able to get a good night's sleep because of " + finalActors[i][j].displayName + "'s guard. "
                            tempResponse += "Some of " + str(finalActors[i][j].currentGameParent.displayName) + "'s wounds healed, and they gained " + str(toGain) + " Health! \n"
                            tempResponse += "\n"
        if response != "":
            await ctx.send(response) #output final response if not empty.
            writeToFile(currentGame.fileName, response)
        if currentGame.currentArenaEvent == 2: #beaver end of day
            await ctx.send("At the end of the day, the rabid beavers disappear from the arena, seemingly having been vaporized. ")
            writeToFile(currentGame.fileName, "At the end of the day, the rabid beavers disappear from the arena, seemingly having been vaporized. ")
        elif currentGame.currentArenaEvent == 3: #flood end of day
            await ctx.send("At the end of the day, the floodwaters recede back to their original coastlines. ")
            writeToFile(currentGame.fileName, "At the end of the day, the floodwaters recede back to their original coastlines. ")
        playersAlive = []
        actuallyAlive = 0
        wolvesStanding = False
        for i in range(len(finalActors)):
            for j in range(len(finalActors[i])):
                #players alive should only have actual players, no wolves or animals
                if finalActors[i][j].currentGameAlive and finalActors[i][j].name != "Giant Wolf" and finalActors[i][j].currentGameParent != None:
                    playersAlive.append(finalActors[i][j])
                if finalActors[i][j].name == "Giant Wolf":
                    wolvesStanding = True
                    actuallyAlive -= 1
                actuallyAlive += 1
        clonesLeft = False
        if actuallyAlive != len(playersAlive): #if these values are different, then there are still clones alive
            clonesLeft = True
        if len(playersAlive) == 1 and clonesLeft:
            await ctx.send(playersAlive[0].displayName + " and their clones are the only ones left standing. ")
            writeToFile(currentGame.fileName, playersAlive[0].displayName + " and their clones are the only ones left standing. ")
        if len(playersAlive) == 1 and wolvesStanding:
            await ctx.send(playersAlive[0].displayName + " and some wolves are the only ones left standing. ")
            writeToFile(currentGame.fileName, playersAlive[0].displayName + " and some wolves are the only ones left standing. ")
        breakoff = False
        response = ""
        if len(playersAlive) == 0: #only case this should happen is when last 2 die to single player traps (happened once before)
            currentGame.winnerDeclared = True
            response += "Nobody came out of the arena alive. There are no winners! "
            currentGame.gameStarted = False
            breakoff = True
            #Endgame leaderboard
            leaderboard = sorted(currentGame.allPlayers, key = lambda x: x.currentGamePlace)
            for i in range(len(leaderboard)):
                response += "\n" + str(i + 1) + ") " + leaderboard[i].displayName + "  (" + str(leaderboard[i].currentGameKills) + ")"
            await ctx.send(response)
            writeToFile(currentGame.fileName, response)
        elif len(playersAlive) == 1: #we have a winner! game is over
            currentGame.winnerDeclared = True
            playersAlive[0].wins += 1
            playersAlive[0].currentStatWins += 1
            winner = playersAlive[0]
            playersAlive[0].currentGamePlace = 0 #fixes leaderboard bug where top two are switched
            #ALL ENDGAME
            response += winner.displayName + " won the Hunger Games! "
            currentGame.gameStarted = False
            breakoff = True
            #Endgame leaderboard
            leaderboard = sorted(currentGame.allPlayers, key = lambda x: x.currentGamePlace)
            for i in range(len(leaderboard)):
                response += "\n" + str(i + 1) + ") " + leaderboard[i].displayName + "  (" + str(leaderboard[i].currentGameKills) + ")"
            await ctx.send(response)
            writeToFile(currentGame.fileName, response)
        else: #multiple people still alive, games continue
            response += "Players still alive: \n"
            count = 0
            toSort = []
            for i in range(len(currentGame.allPlayers)):
                if currentGame.allPlayers[i].currentGameAlive:
                    currentGame.allPlayers[i].daysAlive += 1
                    currentGame.allPlayers[i].currentStatDaysAlive += 1
                    currentGame.allPlayers[i].currentGameDaysAlive += 1
                    toSort.append(currentGame.allPlayers[i])
            toSort = sorted(toSort, key = lambda x: (x.currentGameHealth, x.currentGameKills, x.currentGameWeapons[2], x.currentGameWeapons[1], x.currentGameWeapons[0], x.displayName), reverse = True)
            await ctx.send(response)
            writeToFile(currentGame.fileName, response)
            response = ""
            tempResponse = ""
            for i in range(len(toSort)): #each player info print out
                response += toSort[i].displayName + " (K: " + str(toSort[i].currentGameKills) + ", HP: " + str(toSort[i].currentGameHealth) + "), "
                response += "Current Weaponry: Knives: " + str(toSort[i].currentGameWeapons[0]) + ".  Arrows left: " + str(toSort[i].currentGameWeapons[1]) + ".  Bullets left: " + str(toSort[i].currentGameWeapons[2]) + ". \n"
                if len(response) >= DISCORD_MAX_MESSAGE_LENGTH: #discord character max
                    await ctx.send(tempResponse)
                    writeToFile(currentGame.fileName, tempResponse)
                    response = toSort[i].displayName + " (K: " + str(toSort[i].currentGameKills) + ", HP: " + str(toSort[i].currentGameHealth) + "), "
                    response += "Current Weaponry: Knives: " + str(toSort[i].currentGameWeapons[0]) + ".  Arrows left: " + str(toSort[i].currentGameWeapons[1]) + ".  Bullets left: " + str(toSort[i].currentGameWeapons[2]) + ". \n"
                    tempResponse = ""
                tempResponse += toSort[i].displayName + " (K: " + str(toSort[i].currentGameKills) + ", HP: " + str(toSort[i].currentGameHealth) + "), "
                tempResponse += "Current Weaponry: Knives: " + str(toSort[i].currentGameWeapons[0]) + ".  Arrows left: " + str(toSort[i].currentGameWeapons[1]) + ".  Bullets left: " + str(toSort[i].currentGameWeapons[2]) + ". \n"
                count += 1
            await ctx.send(response)
            writeToFile(currentGame.fileName, response)
            response = "\n" + str(count) + " remaining. "
            await ctx.send(response)
            writeToFile(currentGame.fileName, response)
            response2 = "_ _"
            await ctx.send(response2)
            await ctx.send(response2)
            #print dead players
            response = "Players dead: \n"
            toSort = []
            for i in range(len(currentGame.allPlayers)):
                if not currentGame.allPlayers[i].currentGameAlive:
                    currentGame.allPlayers[i].daysDead += 1
                    currentGame.allPlayers[i].currentStatDaysDead += 1
                    currentGame.allPlayers[i].currentGameDaysDead += 1
                    toSort.append(currentGame.allPlayers[i])
            toSort = sorted(toSort, key = lambda x: (x.currentGamePlace, x.currentGameKills, x.displayName))
            if len(toSort) != 0:
                await ctx.send(response)
                writeToFile(currentGame.fileName, response)
            response = ""
            tempResponse = ""
            for i in range(len(toSort)):
                response += toSort[i].displayName + " (" + str(toSort[i].currentGameKills) + ", Place: " + str(toSort[i].currentGamePlace) + "), \n"
                if len(response) >= DISCORD_MAX_MESSAGE_LENGTH: #discord character max
                    await ctx.send(tempResponse)
                    writeToFile(currentGame.fileName, tempResponse)
                    response = toSort[i].displayName + " (" + str(toSort[i].currentGameKills) + ", Place: " + str(toSort[i].currentGamePlace) + "), \n"
                    tempResponse = ""
                tempResponse += toSort[i].displayName + " (" + str(toSort[i].currentGameKills) + ", Place: " + str(toSort[i].currentGamePlace) + "), \n"
            if response != "":
                await ctx.send(response)
                writeToFile(currentGame.fileName, response)
            response = "\nEnd of Day! "
            currentGame.currentArenaEvent = -1
            await ctx.send(response)
            writeToFile(currentGame.fileName, response)
        for player in currentGame.allPlayers:
            player.savePlayer()
        currentGame.dayOfGame += 1
        if playersAlive == 1: #there was a winner, so we don't need to keep going on with days
            currentGame.gameStarted = False
            breakoff = True
        currentGame.dayOngoing = False
        if breakoff:
            break
        dayCounter += 1
        daysPast += 1
#players: gives list of all players the bot cares about ADMIN ONLY
@bot.command(name='players', pass_context = True, help="prints out list of players, ADMIN ONLY")
@commands.has_role(ADMIN_ROLE)
@asyncio.coroutine
async def players(ctx):
    count = 0
    response = "Players I care about: "
    for member in ctx.message.guild.members:
        if not member.bot: #no bots fighting in games
            for role in member.roles:
                if role.name == "Hunger Games": #only cares about Hunger Games role people
                    response += str(member.display_name)
                    if member != ctx.message.author.guild.members[-1]:
                        response += ", "
                    else:
                        response += ". "
                    count += 1
                    newPlayer = Player(member.display_name)
                    success = newPlayer.loadPlayer()
                    if not success:
                        newPlayer.savePlayer()
    response += "(" + str(count) + " total)"
    await ctx.send(response)
#forceEnd: force the game to end, after the current day has finished. Mostly used for killing the code ADMIN ONLY
@bot.command(name='forceEnd', pass_context = True, help="forces the game to end, ADMIN ONLY", aliases=['gameEnd', 'end'])
@commands.has_role(ADMIN_ROLE)
async def forceEnd(ctx):
    currentGame = 0
    for game in bot.gamesStarted:
        if game.server == ctx.message.guild:
            currentGame = game
    if currentGame != 0:
        currentGame.gameStarted = False
        currentGame.dayOngoing = False
        await ctx.send("Game ended! No wins were allocated. ")
    else:
        await ctx.send("No Game is currently ongoing! ")
#options: gives list of options ADMIN ONLY - more parameters for if you want to change some
#stats: general stats for player. Optional parameter: the display name of the person you want to look up
@bot.command(name='statistics', pass_context=True, help="view all your information. Enter another person's name to view their information.", aliases=['stats'])
async def statistics(ctx, displayName = ""):
    currentGame = 0
    for game in bot.gamesStarted:
        if game.server == ctx.message.guild:
            currentGame = game
    if displayName == "": #if no displayName entered, use the person who called the command
        authorName = ctx.message.author.display_name
    else:
        displayName = displayName.lower()
        for member in ctx.message.guild.members:
            if not member.bot:
                temp = member.display_name.lower()
                if temp.startswith(displayName): #lowercase the name, then search to see if any username starts with the string
                    authorName = member.display_name
                    break
        else: #no usernames found with that display name, so revert back to person who called the command
            authorName = ctx.message.author.display_name
    #remove all nonsense characters
    authorName = ''.join([i if ord(i) < 128 else ' ' for i in authorName])
    authorName = ''.join([i if i != "<" and i != ">" and i != ":" and i != '"' and i != "/" and i != "|" and i != "?" and i != "*" else ' ' for i in authorName])
    newPlayer = Player(authorName)
    newPlayer.loadPlayer()
    if currentGame != 0:
        response = newPlayer.printStats(currentGame.gameStarted)
    else:
        response = newPlayer.printStats(False)
    await ctx.send(response)
#updates: prints big text chunk of updates.
@bot.command(name='updates')
async def updates(ctx):
    response = """Updates:
- NEW FEATURE: Arena Events!
    - There are 5 new arena events, and each day has a percentage chance for them to happen. This should shake up the Arena (literally >:) No other spoilers here!

The next few changes are mostly targeted at balancing, namely the weakness of damage and clones, as well as the one-hit KOs in the end game.
- Initial damage has been increased from 1.0 -> 1.5
- The amount of damage you do in battle is now impacted by your damage stat instead of your luckiness stat.
- Kill Streak: Old: Every kill after 3rd nets you another 1x multiplier (4 kills = x2 damage, 5 = x3, etc.)
               New: Every kill after 3rd nets you another 0.5x multiplier (4 kills = x1.5 damage, 5 = x2, etc.)
- Knives now scale linearly at first, then logarithmically, instead of linearly the entire time
- Clones now heal you at the end of day, since they can protect the camp while you get a good night's sleep. Each clone alive means more eyes so more healing.
- Clone spawn chance increased from 20% -> 35%
- Luckiness: Old: All rolls then took your luckiness, divided it by 10, added it to your roll, and that was your final number.
             New: All rolls take your luckiness, divide it by 12, add it to your roll, and that's your final number.

Quality of Life updates:
- In the case that no one wins, the game doesn't crash anymore.
- The probability that you encounter another player increases as the arena closes.
- Other minor bug fixes.

Last updated: 3/19/2020 @11:19
"""
    await ctx.send(response)
#changeStats: changes stats for player if legal. Will fail if player is in a game.
@bot.command(name='changeStats', pass_context=True, help="change your statistic layout here. Needs three numbers, in the order   health percent   damage percent   luckiness percent   that sum to 400 or less and none are less than 0. Example: !changeStats 3 2 5", aliases=['changestats', 'cstats', 'changeStatistics', 'changestatistics'])
async def changeStats(ctx, health = -1.0, damage = -1.0, luckiness = -1.0):
    currentGame = 0
    for game in bot.gamesStarted:
        if game.server == ctx.message.guild:
            currentGame = game
    change = True
    if currentGame != 0:
        if currentGame.gameStarted:
            for i in range(len(currentGame.allPlayers)):
                if currentGame.allPlayers[i].name == ctx.message.author.display_name:
                    if currentGame.allPlayers[i].currentGameAlive:
                        change = False
                        response = "You are in a game right now! You can change your stats when you die. "
    if change:
        try:
            health = float(health)
            damage = float(damage)
            luckiness = float(luckiness)
        except:
            response = "Error: Enter decimals numbers only! "
        response = ""
        if health == -1 or damage == -1 or luckiness == -1:
            response = "Error: Enter numbers for all three variables. Use no commas between variables."
        newPlayer = Player(ctx.message.author.display_name)
        success = newPlayer.loadPlayer()
        if not success:
            newPlayer.savePlayer()
        if response != "Error: Enter decimals numbers only! " and response != "Error: Enter numbers for all three variables. Use no commas between variables.":
            response = newPlayer.changeStats(health, damage, luckiness)
            newPlayer.savePlayer()
    await ctx.send(response)
#changeCloneStats: changes the clone stats for player if legal. Will fail if player is in game.
@bot.command(name='changeCloneStats', pass_context=True, help="change your clone statistic layout here. Needs three numbers, in the order   least number of health to be at    health to lose and give to clone   percent of weaponry to give    ,none of which are less than 0. Set 'health to lose and give to clone' to 0 to never split. Example: !changeCloneStats 3 4 2", aliases=['changeclonestats', 'ccstats', 'changecstats', 'changeCStats'])
async def changeCloneStats(ctx, healthReq = -1.0, healthToSplit = -1.0, weaponryPercentage = -1.0):
    currentGame = 0
    for game in bot.gamesStarted:
        if game.server == ctx.message.guild:
            currentGame = game
    change = True
    if currentGame != 0:
        if currentGame.gameStarted:
            for i in range(len(currentGame.allPlayers)):
                if currentGame.allPlayers[i].name == ctx.message.author.display_name:
                    if currentGame.allPlayers[i].currentGameAlive:
                        change = False
                        response = "You are in a game right now! You can change your stats when you die. "
    if change:
        try:
            healthReq = float(healthReq)
            healthToSplit = float(healthToSplit)
            weaponryPercentage = float(weaponryPercentage)
        except:
            response = "Error: Enter decimals numbers only! "
        response = ""
        if healthReq == -1 or weaponryPercentage == -1 or healthToSplit == -1:
            response = "Error: Enter numbers for all three variables. Use no commas between variables."
        if healthToSplit >= healthReq:
            response = "Error: The health you're going to lose must be less than the health you want to be at when you make a clone. Otherwise you'll die. "
        newPlayer = Player(ctx.message.author.display_name)
        success = newPlayer.loadPlayer()
        if not success:
            newPlayer.savePlayer()
        if response != "Error: Enter decimals numbers only! " and response != "Error: Enter numbers for all three variables. Use no commas between variables." and response != "Error: The health you're going to lose must be less than the health you want to be at when you make a clone. Otherwise you'll die. ":
            response = newPlayer.changeCloneStats(healthReq, healthToSplit, weaponryPercentage)
            newPlayer.savePlayer()
    await ctx.send(response)
#leaderboard: show leaderboard of overall wins. Takes a paramter for number of top places to show. enter nonpositive integer to see all places
@bot.command(name='leaderboard', help="Displays leaderboard of most overall wins.", aliases=['leaderboards', 'lb'])
async def leaderboard(ctx, places = 10):
    response = "Leaderboard: \n"
    leaderboard = []
    toDisplay = 0
    for member in ctx.message.guild.members:
        if not member.bot:
            for role in member.roles:
                if role.name == "Hunger Games":
                    authorName = ''.join([i if ord(i) < 128 else ' ' for i in member.display_name])
                    authorName = ''.join([i if i != "<" and i != ">" and i != ":" and i != '"' and i != "/" and i != "|" and i != "?" and i != "*" else ' ' for i in authorName])
                    newPlayer = Player(authorName)
                    newPlayer.loadPlayer()
                    leaderboard.append(newPlayer)
                    toDisplay += 1
    sortedPlayers = sorted(leaderboard, key=lambda x: x.wins, reverse = True)
    if toDisplay > places and places > 0: #if places is a legal integer, it'll limit toDisplay. Otherwise toDisplay untouched, and will print everything
        toDisplay = places
    i = 1
    while i <= toDisplay:
        response += str(i) + ". " + sortedPlayers[i - 1].name + ": " + str(sortedPlayers[i - 1].wins) + " wins. \n"
        i += 1
    await ctx.send(response)
#gameFiles: display all game files in the folder
@bot.command(name='gameFiles', help="Displays all the past games that have records.", aliases=['games', 'history'])
async def gameFiles(ctx):
    response = "Files: \n"
    i = 1
    for file in os.listdir(path):
        if file.endswith(".txt") and file.startswith(ctx.message.guild.name): #only txt files, check if name is correct
            response += str(i) + ". " + file + "\n"
            i += 1
    await ctx.send(response)
#openFile: get game file, and get stuff for specific user.
@bot.command(name='openFile', help="opens the file you inputted and gets all related info for the person you want (no person for your information)", aliases=['OF', 'oF'])
async def openFile(ctx, gameFile, displayName = ""):
    fileToOpen = ""
    for file in os.listdir(path):
        if file.endswith(".txt") and file.startswith(ctx.message.guild.name):
            if gameFile in file:
                fileToOpen = file
    if fileToOpen == "":
        await ctx.send("No game file found with that name! ")
        return 0
    if displayName == "": #no displayName entered, use command caller
        authorName = ctx.message.author.display_name
    else:
        #same algorithm as above for finding displayName entered
        displayName = displayName.lower()
        for member in ctx.message.guild.members:
            if not member.bot:
                temp = member.display_name.lower()
                if temp.startswith(displayName):
                    authorName = member.display_name
                    break
        else: #none found, user command caller
            authorName = ctx.message.author.display_name
    #strip name of file illegal symbols
    authorName = ''.join([i if ord(i) < 128 else ' ' for i in authorName])
    authorName = ''.join([i if i != "<" and i != ">" and i != ":" and i != '"' and i != "/" and i != "|" and i != "?" and i != "*" else ' ' for i in authorName])
    f = open(os.path.join(path, fileToOpen), "r")
    toReturn = f.read().splitlines()
    f.close()
    response = ""
    tempResponse = ""
    placeSeen = False
    currentlyFighting = False
    for i in range(len(toReturn)):
        if authorName in toReturn[i] or "arena" in toReturn[i] or "ARENA EVENT" in toReturn[i] or "Day" in toReturn[i] or currentlyFighting: #beginning of day stuff important, everything with author name important
            #if he's currently fighting, all text needs to be printed.
            if ("accidentally" in toReturn[i] or "purposefully" in toReturn[i]) and authorName in toReturn[i]: #any of these means the author is currently fighting. Thus everything around it needs to be printed.
                currentlyFighting = True
            if "Place:" in toReturn[i] and placeSeen: #the placement of the author was seen already, and since they're dead, no need to print it again
                continue
            if "Place:" in toReturn[i] and not placeSeen: #first time we see placement. author is dead.
                placeSeen = True
            response += toReturn[i] + "\n"
            if len(response) >= DISCORD_MAX_MESSAGE_LENGTH: #discord character max
                await ctx.send(tempResponse)
                response = toReturn[i] + "\n"
                tempResponse = ""
            tempResponse += toReturn[i] + "\n"
            if ("agrees." in toReturn[i] or "killed" in toReturn[i]) and currentlyFighting: #end of fighting trigger
                currentlyFighting = False
    await ctx.send(response)

#on join server: do nothing
@bot.event
async def on_member_join(member):
    pass
    
bot.run(TOKEN)