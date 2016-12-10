# A Sample Carrom Agent to get you started. The logic for parsing a state
# is built in

from Utils import *
from thread import *
import time
import socket
import sys
import argparse
import random
import ast
import math
import pygame
import pymunk
import pymunk.pygame_util

# Parse arguments

parser = argparse.ArgumentParser()

parser.add_argument('-np', '--num-players', dest="num_players", type=int,
					default=1,
					help='1 Player or 2 Player')
parser.add_argument('-p', '--port', dest="port", type=int,
					default=12121,
					help='port')
parser.add_argument('-rs', '--random-seed', dest="rng", type=int,
					default=0,
					help='Random Seed')
parser.add_argument('-c', '--color', dest="color", type=str,
					default="Black",
					help='Legal color to pocket')
args = parser.parse_args()


host = '127.0.0.1'
port = args.port
num_players = args.num_players
random.seed(args.rng)  # Important
color = args.color

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.connect((host, port))


def isObstacle(coin, coin1, pocket):
    coinPos = coin
    coin1Pos = coin1
    pocketPos = pocket.body.position

    slope1 = (coinPos[1]-pocketPos[1])/(coinPos[0]-pocketPos[0])
    slope2 = (coin1Pos[1]-pocketPos[1])/(coin1Pos[0]-pocketPos[0])
    if(abs(abs(math.degrees(math.atan(slope1)))-abs(math.degrees(math.atan(slope2))))<=5 and ((coinPos[1]>105.0 and coin1Pos[1]>105.0) or (coinPos[1]<175.0 and coin1Pos[1]<175.0))):
        return True
    else:
        return False

def angleFin(coinFin, pocketFin):
    tempCoin = coinFin
    tempPocket = pocketFin.body.position
    slope = (tempPocket[1]-tempCoin[1])/(tempPocket[0]-tempCoin[0])
    angle = 0
    if(tempCoin[1]>175.0 and tempPocket[1]>175.0):
        angle = math.degrees(math.atan(slope))
        if(angle<0):
            angle = angle + 180
    elif(tempCoin[1]<105.0 and tempPocket[1]<105.0 and slope>0):
        angle = math.degrees(math.atan(slope))+180
    elif(tempCoin[1]<105.0 and tempPocket[1]<105.0 and slope<0):
        angle = math.degrees(math.atan(slope))
        # if(angle<-45):
        #     angle = angle + 180
    return angle

def angleStriker(coinFin, pos):
    tempCoin = coinFin
    slope = (140.0-tempCoin[1])/(pos-tempCoin[0])
    angle = 0.0

    if(tempCoin[1]>175.0):
        angle = math.degrees(math.atan(slope))
        if(angle<0):
            angle = angle + 180.0
    elif(tempCoin[1]<105.0 and slope>0):
        angle = math.degrees(math.atan(slope))+180.0
        # if(angle>225):
        #     angle = 105
    elif(tempCoin[1]<105.0 and slope<0):
        angle = math.degrees(math.atan(slope))
        # if(angle<-45):
        #     angle = angle + 180s
    else:
        if(tempCoin[0]<170.0):
            pos = 170.0
            angle = 180.0
        elif(tempCoin[1]>630.0):
            pos = 630.0
            angle = 0.0
        else:
            if(tempCoin[0]<400.0):
                pos = tempCoin[0]+(STRIKER_RADIUS+COIN_RADIUS+5.0)
                angle = 180.0
            elif(tempCoin[0]>400.0):
                pos = tempCoin[0]-(STRIKER_RADIUS+COIN_RADIUS+5.0)
                angle = 0.0
    return angle, pos 


def isValid(coinFin, pocketFin):

    tempCoin = coinFin
    tempPocket = pocketFin.body.position
    slope = (tempPocket[1]-tempCoin[1])/(tempPocket[0]-tempCoin[0])
    pos1 = (tempCoin[0])+(140.0-tempCoin[1])*(tempPocket[0]-tempCoin[0])/(tempPocket[1]-tempCoin[1])
    pos = (pos1-170)/460
    angle1 = angleFin(coinFin, pocketFin)
    if(angle1<-45):
        angle1 = angle1+180

    if(pos>=0 and pos<=1 and angle1>=-45 and angle1<=225 and ((tempCoin[1]<105.0 and tempPocket[1]<105.0) or (tempCoin[1]>175.0 and tempPocket[1]>175.0))):
        return True

    else:
        return False


# Given a message from the server, parses it and returns state and action


def parse_state_message(msg):
    s = msg.split(";REWARD")
    s[0] = s[0].replace("Vec2d", "")
    reward = float(s[1])
    state = ast.literal_eval(s[0])
    return state, reward

def directHit(coinFin, pocketFin):
    tempCoin = coinFin
    tempPocket = pocketFin.body.position

    slope = (tempPocket[1]-tempCoin[1])/(tempPocket[0]-tempCoin[0])
    pos = (tempCoin[0])+(140.0-tempCoin[1])*(tempPocket[0]-tempCoin[0])/(tempPocket[1]-tempCoin[1])

    if(pos>=170 and pos<=630):
        pos = (pos-170)/460
        angle = angleFin(coinFin, pocketFin)
        if(coinFin[1]<105):
            #print(dist(coinFin, tempPocket))
            if(dist(coinFin, tempPocket) < 90.0):
                force = 0.003
            elif(dist(coinFin, tempPocket) < 120.0):
                force = 0.005
            elif(dist(coinFin, tempPocket) < 300.0):
                force = 0.021
            else:
                force = 0.031
        else:
            force = 0.06
            print(dist(coinFin, (pos*460.0+170.0, 140)))
            if(dist(coinFin, tempPocket) < 90.0):
                if(dist(coinFin, (pos*460.0+170.0, 140)) > 700):
                    force = 0.07
                elif(dist(coinFin, (pos*460.0+170.0, 140)) > 600):
                    force = 0.051
                else:
                    force = 0.059
            elif(dist(coinFin, tempPocket) < 150.0):
                force = 0.055
            else:
                force = 0.058

    return pos, angle, force

def strikerObstacle(state, pos):
    blackPos = state["Black_Locations"]
    whitePos = state["White_Locations"]
    redPos = state["Red_Location"]

    obstacleFlag = False
    for white1 in whitePos:
        if(white1[1]>105.0 and white1[1]<175.0):
            obstacleFlag = obstacleFlag or (abs(white1[0]-pos)<STRIKER_RADIUS+COIN_RADIUS)
    for black1 in blackPos:
        if(black1[1]>105.0 and black1[1]<175.0):
            obstacleFlag = obstacleFlag or (abs(black1[0]-pos)<STRIKER_RADIUS+COIN_RADIUS)
    for red1 in redPos:
        if(red1[1]>105.0 and red1[1]<175.0):
            obstacleFlag = obstacleFlag or (abs(red1[0]-pos)<STRIKER_RADIUS+COIN_RADIUS)

    return obstacleFlag

def straightCut(coinFin, pocketFin):
    print("Straight cut")
    if(pocketFin.body.position[0]<400):
        pos = coinFin[0] + 15.0
    else:
        pos = coinFin[0] - 15.0

    if(pos<170):
        pos = 200.0
        angle, pos = angleStriker(coinFin, pos)
        force = 0.8
    elif(pos>630):
        pos = 600.0
        angle, pos = angleStriker(coinFin, pos)
        force = 0.8
    else:
        angle = 90
        force = 0.33

    pos = (pos-170.0)/460

    return pos, angle, force

first = False

def coinSelect(coinFin, pockets):
    if(coinFin[1]>175.0):
        if(coinFin[0]<400.0):
            pocketFin = pockets[3]
        else:
            pocketFin = pockets[2]
        if(coinFin[0]<=170.0):
            pos = 170.0
            angle, pos = angleStriker(coinFin, 170.0)
            if(dist(coinFin, (pos, 140)) > 600.0):
                if (coinFin[1] > coinFin[0]):
                    force = 0.1
                else:
                    force = 0.049
            else:
                force = 0.0525
            pos = (pos-170.0)/460.0
        elif(coinFin[0]>=630.0):
            pos = 630.0
            angle, pos = angleStriker(coinFin, 630.0)
            if(dist(coinFin, (pos, 140)) > 600.0):
                if (coinFin[1] > coinFin[0]):
                    force = 0.1
                else:
                    force = 0.049
            else:
                force = 0.0525
            pos = (pos-170.0)/460
        else:
            pos, angle, force = straightCut(coinFin, pocketFin)
    else:
        if(coinFin[1] < 105.0):
            if(coinFin[0]<170.0):
                pocketFin = pockets[0]
                pos = 0.0
                force = 0.05
                angle, pos = angleStriker(coinFin, 170.0)
                if(angle>225.0):
                    angle = 90.0
                    force = 0.7
                pos = (pos-170.0)/460

            elif(coinFin[0]>630.0):
                pocketFin = pockets[1]
                pos = 1.0
                force = 0.05
                angle, pos = angleStriker(coinFin, 630.0)
                if(angle<-45.0):
                    angle = 90.0
                    force = 0.7
                pos = (pos-170.0)/460

            else:
                if(coinFin[0]<400.0):
                    pos = 630.0
                    force = 0.12
                    angle, pos = angleStriker(coinFin, pos)
                    pos = 1.0
                else:
                    pos = 170.0
                    force = 0.12
                    angle, pos = angleStriker(coinFin, pos)
                    pos = 0.0
        else:
            if(coinFin[0]<170.0):
                pocketFin = pockets[0]
                pos = 0.0
                force = 0.1
                angle, pos = angleStriker(coinFin, 170.0)
                if(angle>225.0):
                    angle = 90.0
                    force = 0.7
                pos = (pos-170.0)/460

            elif(coinFin[0]>630.0):
                pocketFin = pockets[1]
                pos = 1.0
                force = 0.1
                angle, pos = angleStriker(coinFin, 630.0)
                if(angle<-45.0):
                    angle = 90.0
                    force = 0.7
                pos = (pos-170.0)/460

            else:
                if(coinFin[0]<400.0):
                    pos = 630.0
                    force = 0.21
                    angle, pos = angleStriker(coinFin, pos)
                    pos = (pos-170.0)/460.0
                else:
                    pos = 170.0
                    force = 0.22
                    angle, pos = angleStriker(coinFin, pos)
                    pos = (pos-170.0)/460.0

    return pos, angle, force



def agent_1player(state):

    flag = 1
    # print state
    try:
        state, reward = parse_state_message(state)  # Get the state and reward
    except:
        pass

    # Assignment 4: your agent's logic should be coded here
    space = pymunk.Space(threaded=True)
    init_space(space)
    init_walls(space)
    pockets = init_pockets(space)


    blackPos = state["Black_Locations"]
    whitePos = state["White_Locations"]
    redPos = state["Red_Location"]
    score = state["Score"]
    # score = 15
    
    # if(len(blackPos) != 0):
    #     coinFin = blackPos[0]
    # elif(len(whitePos) != 0):
    #     coinFin = whitePos[0]
    # else:
    #     coinFin = redPos[0]
    # pocketFin = pockets[0]
    if(score==0):
        pos = 0.4
        force = 0.9
        angle = 90.0
        
    else:
        coinFin = None
        pocketFin = None

        obstacleFlag = False
        for red in redPos:
                for pocket in pockets:
                    obstacleFlag = False
                    for white1 in whitePos:
                        obstacleFlag = obstacleFlag or isObstacle(red, white1, pocket)
                    for black1 in blackPos:
                        obstacleFlag = obstacleFlag or isObstacle(red, black1, pocket)
                    if(obstacleFlag==False):
                        if(isValid(red, pocket)):
                            coinFin = red
                            pocketFin = pocket
                            break
                        else:
                            obstacleFlag = True

        if((coinFin == None) or (pocketFin == None)):
            for white in whitePos:
                for pocket in pockets:
                    obstacleFlag = False
                    for white1 in whitePos:
                        if(white1!=white):
                            obstacleFlag = obstacleFlag or isObstacle(white, white1, pocket)
                    for black1 in blackPos:
                        obstacleFlag = obstacleFlag or isObstacle(white, black1, pocket)
                    for red1 in redPos:
                        obstacleFlag = obstacleFlag or isObstacle(white, red1, pocket)
                    if(obstacleFlag==False):
                        if(isValid(white, pocket)):
                            coinFin = white
                            pocketFin = pocket
                            break
                        else:
                            obstacleFlag = True

        if((coinFin == None) or (pocketFin == None)):
            for black in blackPos:
                for pocket in pockets:
                    obstacleFlag = False

                    obs = False
                    for black1 in blackPos:
                        if(black1!=black):
                            obstacleFlag = obstacleFlag or isObstacle(black, black1, pocket)
                    for white1 in whitePos:
                        obstacleFlag = obstacleFlag or isObstacle(black, white1, pocket)
                    for red1 in redPos:
                        obstacleFlag = obstacleFlag or isObstacle(black, red1, pocket)
                    if(obstacleFlag==False):
                        if(isValid(black, pocket)):
                            coinFin = black
                            pocketFin = pocket
                            break
                        else:
                            obstacleFlag = True
            

        if((coinFin == None) or (pocketFin == None)):
            pass1 = False
            # while(pass):
            # if(len(redPos) != 0):
            #     coinFin = redPos[0]
            # elif(len(whitePos) != 0):
            #     coinFin = whitePos[0]
            # else:
            #     coinFin = blackPos[0]

            for red in redPos:
                pos, angle, force = coinSelect(red, pockets)
                if(strikerObstacle(state, pos*460.0+170.0)==False):
                    pass1 = True
                    coinFin = red
                    break
            if(pass1==False):
                for white in whitePos:
                    pos, angle, force = coinSelect(white, pockets)
                    if(strikerObstacle(state, pos*460.0+170.0)==False):
                        pass1 = True
                        coinFin = white
                        break
            if(pass1==False):
                for black in blackPos:
                    pos, angle, force = coinSelect(black, pockets)
                    if(strikerObstacle(state, pos*460.0+170.0)==False):
                        pass1 = True
                        coinFin = black
                        break
            if(score<=12):
                force = 0.6

        else:
            print("Direct hit")
            pos, angle, force = directHit(coinFin, pocketFin)
        
        print(coinFin)
       # print(dist(coinFin, (pos*460.0+170.0, 140.0)))


    a = str(pos) + ',' + \
        str(angle) + ',' + str(force)
    # print("sent info:" + a)
    # a = str(random.random()) + ',' + \
    #     str(random.randrange(-45, 225)) + ',' + str(random.random())

    try:
        s.send(a)
    except Exception as e:
        print "Error in sending:",  a, " : ", e
        print "Closing connection"
        flag = 0

    return flag


def agent_2player(state, color):

	flag = 1

	try:
		state, reward = parse_state_message(state)  # Get the state and reward
	except:
		pass

	# Assignment 4: your agent's logic should be coded here
	space = pymunk.Space(threaded=True)
	init_space(space)
	init_walls(space)
	pockets = init_pockets(space)


	blackPos = state["Black_Locations"]
	whitePos = state["White_Locations"]
	redPos = state["Red_Location"]
	score = state["Score"]
	
	# if(len(blackPos) != 0):
	#     coinFin = blackPos[0]
	# elif(len(whitePos) != 0):
	#     coinFin = whitePos[0]
	# else:
	#     coinFin = redPos[0]
	# pocketFin = pockets[0]
	
	coinFin = None
	pocketFin = None

	obstacleFlag = False
	if(score > 0):
		for red in redPos:
				for pocket in pockets:
					obstacleFlag = False
					for white1 in whitePos:
						obstacleFlag = obstacleFlag or isObstacle(red, white1, pocket)
					for black1 in blackPos:
						obstacleFlag = obstacleFlag or isObstacle(red, black1, pocket)
					if(obstacleFlag==False):
						if(isValid(red, pocket)):
							coinFin = red
							pocketFin = pocket
							break
						else:
							obstacleFlag = True

	if((len(redPos) == 1 and score == 8) == False):
		if(color == "White"):
			if((coinFin == None) or (pocketFin == None)):
				for white in whitePos:
					for pocket in pockets:
						obstacleFlag = False
						for white1 in whitePos:
							if(white1!=white):
								obstacleFlag = obstacleFlag or isObstacle(white, white1, pocket)
						for black1 in blackPos:
							obstacleFlag = obstacleFlag or isObstacle(white, black1, pocket)
						for red1 in redPos:
							obstacleFlag = obstacleFlag or isObstacle(white, red1, pocket)
						if(obstacleFlag==False):
							if(isValid(white, pocket)):
								coinFin = white
								pocketFin = pocket
								break
							else:
								obstacleFlag = True
		else:
			if((coinFin == None) or (pocketFin == None)):
				for black in blackPos:
					for pocket in pockets:
						obstacleFlag = False

						obs = False
						for black1 in blackPos:
							if(black1!=black):
								obstacleFlag = obstacleFlag or isObstacle(black, black1, pocket)
						for white1 in whitePos:
							obstacleFlag = obstacleFlag or isObstacle(black, white1, pocket)
						for red1 in redPos:
							obstacleFlag = obstacleFlag or isObstacle(black, red1, pocket)
						if(obstacleFlag==False):
							if(isValid(black, pocket)):
								coinFin = black
								pocketFin = pocket
								break
							else:
								obstacleFlag = True
		

	if((coinFin == None) or (pocketFin == None)):
		pass1 = False
		# while(pass):
		# if(len(redPos) != 0):
		#     coinFin = redPos[0]
		# elif(len(whitePos) != 0):
		#     coinFin = whitePos[0]
		# else:
		#     coinFin = blackPos[0]
		if(score > 0):
			for red in redPos:
				pos, angle, force = coinSelect(red, pockets)
				if(strikerObstacle(state, pos*460.0+170.0)==False):
					pass1 = True
					coinFin = red
					break

		if(color == "White"):
			if(pass1==False):
				for white in whitePos:
					pos, angle, force = coinSelect(white, pockets)
					if(strikerObstacle(state, pos*460.0+170.0)==False):
						pass1 = True
						coinFin = white
						break
		else:
			if(pass1==False):
				for black in blackPos:
					pos, angle, force = coinSelect(black, pockets)
					if(strikerObstacle(state, pos*460.0+170.0)==False):
						pass1 = True
						coinFin = black
						break
		# if(score<=12):
		# 	force = 0.6

	else:
		print("Direct hit")
		pos, angle, force = directHit(coinFin, pocketFin)
	
	print(coinFin)
   # print(dist(coinFin, (pos*460.0+170.0, 140.0)))
   
	a = str(pos) + ',' + \
		str(angle) + ',' + str(force)

	# Can be ignored for now
	# a = str(random.random()) + ',' + \
	#     str(random.randrange(-45, 225)) + ',' + str(random.random())

	try:
		s.send(a)
	except Exception as e:
		print "Error in sending:",  a, " : ", e
		print "Closing connection"
		flag = 0

	return flag


while 1:
	state = s.recv(1024)  # Receive state from server
	if num_players == 1:
		if agent_1player(state) == 0:
			break
	elif num_players == 2:
		if agent_2player(state, color) == 0:
			break
s.close()
