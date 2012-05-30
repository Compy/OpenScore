'''
Created on May 28, 2012

@author: Jimmy
'''

import sys, re

frame_scores = []

for i in range(12):
    frame_scores.append(-1)

parse_frames = lambda game: re.findall('X|..|.', game)

# Return values of a single frame
def frame_values(frame):
    if frame == "X":
        return [10]
    elif frame[-1] == "/":
        val = int(frame[0])
        return [val, 10 - val]
    else:
        return [int(s) for s in frame]

# Total the score of an entire game string
def score(game):
    score = 0
    max_turns = 10 * 2 + 3
    bonus = [1] * max_turns
    i = 0
    
    game = game.replace('-', '0')
    frames = parse_frames(game)
    
    for count, frame in enumerate(frames):
        for v in frame_values(frame):
            score += v * bonus[i]
            i += 1
            
        if count < 9:
            if frame == "X":
                bonus[i] += 1
                bonus[i+1] += 1
            elif frame[-1] == "/":
                bonus[i] += 1
                
    print bonus
    return score

# Given a game string, find the score in each frame
def getIndividualFrameScores(game):
    game = game.replace('-','0')
    frames = parse_frames(game)
    
    for count, frame in enumerate(frames):
        print frame_values(frame)
    
    print frames

if __name__ == '__main__':
    print score("4/4")