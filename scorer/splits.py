'''
Created on Jun 11, 2012

@author: Jimmy
'''
splits = []
splits.append((7,10))
splits.append((6,7))
splits.append((4,6))
splits.append((2,10))
splits.append((2,4,10))
splits.append((4,9))
splits.append((3,8))
splits.append((2,9))
splits.append((6,8))
splits.append((4,10))
splits.append((7,9))
splits.append((8,10))
splits.append((5,7))
splits.append((5,10))
splits.append((5,7,10))
splits.append((3,7))
splits.append((2,7))
splits.append((3,10))
splits.append((2,7,10))
splits.append((3,7,10))
splits.append((4,6,7,10))
splits.append((2,3))
splits.append((4,5))
splits.append((5,6))
splits.append((7,8))
splits.append((8,9))
splits.append((9,10))
splits.append((4,6,9))
splits.append((4,6,8))
splits.append((4,6,7,8,10))
splits.append((4,6,7,9,10))
splits.append((3,4,6,7,10))
splits.append((2,4,6,7,10))
splits.append((2,4,6,7,8,10))
splits.append((3,4,6,7,9,10))
splits.append((4,7,10))
splits.append((6,7,10))

def isSplit(pindeck_state):
    pins_standing = []
    counter = 1
    for p in pindeck_state:
        if p == True:
            pins_standing.append(counter)
        counter += 1
        
    pins_standing = tuple(pins_standing)
        
    match = [item for item in splits if pins_standing == item]
    return len(match) > 0
            