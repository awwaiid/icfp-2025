
class Room:
    def __init__(self, room_index=None, label=None):
        self.room_index = room_index  # true room "index" 
        self.label = label  # which is 0, 1, 2, or 3
        self.paths = []  # array of paths for how we got here
        self.door_connections = {}  # for each door (0-5), labels of rooms we are connected to
        self.doors = [None] * 6  # array of doors (0-5) and their related rooms

