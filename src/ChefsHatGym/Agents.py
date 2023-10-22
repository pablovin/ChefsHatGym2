# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import numpy as np
import socket
import random
from numbers import Number
from ChefsHatGym.Rewards import RewardOnlyWinning, RewardPerformanceScore
import time
import requests
import pickle
import base64
import json
from functools import wraps
import os

def encodeb64(data):
    return base64.b64encode(pickle.dumps(data)).decode()

def decodeb64(data):
    return pickle.loads(base64.b64decode(data.encode()))

class IAgent():
    """This is the Agent class interface. Every new Agent must inherit from this class and implement the methods below."""
    __metaclass__ = ABCMeta
    name = "" #: Class attribute to store the name of the agent
    saveModelIn = "" #: Class attribute path to a folder acessible by this agent to save/load from
    id = "0"
    room_id = "0"
    ip = socket.gethostbyname(socket.gethostname())
    port = 8080
    exe_path = None
    
    @abstractmethod
    def __init__(self, name, saveModelIn, _):
        """Constructor method.

        :param name: The name of the Agent (must be a unique name).
        :type name: str

        :param saveModelIn: a folder acessible by this agent to save/load from
        :type saveModelIn: str

        :param _: Other parameters that your Agent must need
        :type _: obj, optional

        """
        pass

    @abstractmethod
    def getAction(self, observations):
        """This method returns one action given the observation parameter.

                :param observations: The observation is an int data-type ndarray.
                                    The observation array has information about the board game, the player's hand, and possible actions.
                                    This array must have the shape of (228, ) as follows:
                                    The first 11 elements represent the board game card placeholder (the pizza area).
                                    The game cards are represented by an integer, where 0 (zero) means no card.
                                    The following 17 elements (from index 11 to 27) represent the player hand cards in the sequence.
                                    By the end, the last 200 elements (from index 28 to 227) represent all possible actions in the game.
                                    The allowed actions are filled with one, while invalid actions are filled with 0.
                :type observations: ndarray
                :return: The action array with 200 elements, where the choosen action is the index of the highest value
                :rtype: ndarray
        """

        pass

    @abstractmethod
    def getReward(self, info, stateBefore, stateAfter):
        """The Agent reward method, called inside each evironment step.

                :param info: [description]
                :type info: dict

                :param stateBefore: The observation before the action happened is an int data-type ndarray.
                                    The observationBefore array has information (before the player's action) about the board game, the player's hand, and possible actions.
                                    This array must have the shape of (228, ) as follows:
                                    The first 11 elements represent the board game card placeholder (the pizza area).
                                    The game cards are represented by an integer, where 0 (zero) means no card.
                                    The following 17 elements (from index 11 to 27) represent the player hand cards in the sequence.
                                    By the end, the last 200 elements (from index 28 to 227) represent all possible actions in the game.
                                    The allowed actions are filled with one, while invalid actions are filled with 0.
                :type stateBefore: ndarray

                :param stateAfter: The observation after the action happened is an int data-type ndarray.
                                    The observationBefore array has information (after the player's action) about the board game, the player's hand, and possible actions.
                                    This array must have the shape of (228, ) as follows:
                                    The first 11 elements represent the board game card placeholder (the pizza area).
                                    The game cards are represented by an integer, where 0 (zero) means no card.
                                    The following 17 elements (from index 11 to 27) represent the player hand cards in the sequence.
                                    By the end, the last 200 elements (from index 28 to 227) represent all possible actions in the game.
                                    The allowed actions are filled with one, while invalid actions are filled with 0.
                :type stateAfter: ndarray

                """

        pass

    @abstractmethod
    def observeOthers(self, envInfo):
        """This method gives the agent information of other playes actions. It is called after each other player action.

        :param envInfo: [description]
        :type envInfo: [type]
        """

        pass

    @abstractmethod
    def actionUpdate(self,  observation, nextObservation, action, envInfo):
        """This method that is called after the Agent's action.

                :param observation: The observation is an int data-type ndarray.
                                    The observation array has information about the board game, the player's hand, and possible actions.
                                    This array must have the shape of (228, ) as follows:
                                    The first 11 elements represent the board game card placeholder (the pizza area).
                                    The game cards are represented by an integer, where 0 (zero) means no card.
                                    The following 17 elements (from index 11 to 27) represent the player hand cards in the sequence.
                                    By the end, the last 200 elements (from index 28 to 227) represent all possible actions in the game.
                                    The allowed actions are filled with one, while invalid actions are filled with 0.
                :type observation: ndarray
                :param nextObservation: The nextObservation is an int data-type ndarray.
                                    The nextObservation array has information about the board game, the player's hand, and possible actions.
                                    This array must have the shape of (228, ) as follows:
                                    The first 11 elements represent the board game card placeholder (the pizza area).
                                    The game cards are represented by an integer, where 0 (zero) means no card.
                                    The following 17 elements (from index 11 to 27) represent the player hand cards in the sequence.
                                    By the end, the last 200 elements (from index 28 to 227) represent all possible actions in the game.
                                    The allowed actions are filled with one, while invalid actions are filled with 0.
                :type nextObservation: ndarray
                :param action: The action array with 200 elements, where the choosen action is the index of the highest value
                :type action: ndarray
                :param envInfo: [description]
                :type envInfo: [type]
                """

        pass

    @abstractmethod
    def matchUpdate(self,  envInfo):
        """This method that is called by the end of each match. This is an oportunity to update the Agent with information gathered in the match.

                :param envInfo: [description]
                :type envInfo: [type]
                """
        pass

class RemoteAgent(IAgent):
    def __init__(self, name="NAIVE", id="0", room_id="0", agentManager="http://127.0.0.1:8000/", gameManager="http://127.0.0.1:9000/"):
        self.name = name
        self.id = id
        self.room_id = room_id
        self.agentManager = agentManager
        self.gameManager = gameManager
    
    def decode_response(f):
        @wraps(f)
        def decorator(self, *args):
            try:
                resp = requests.post(
                    f"{self.agentManager}{f.__name__}",
                    data=json.dumps({"id": self.id, "pickle": encodeb64(args)}),
                    timeout=120,
                    headers={'Content-type': 'application/json'},
                    verify=False
                ).json()
                dec = decodeb64(resp["pickle"])
                return f(self, dec)
            except Exception as e:
                return None
        return decorator
    
    @decode_response
    def getAction(self, *args):
        requests.post(
            f"{self.gameManager}/keep_room_alive",
            data=json.dumps({"id": self.room_id}),
            timeout=120,
            headers={'Content-type': 'application/json'},
            verify=False
        )
        return args[0] if isinstance(args[0], np.ndarray) else np.zeros(200)

    @decode_response
    def actionUpdate(self, *args):
        return args[0]

    @decode_response
    def observeOthers(self, *args):
        return args[0]

    @decode_response
    def matchUpdate(self, *args):
        return args[0]

    @decode_response
    def getReward(self, *args):
        return args[0] if isinstance(args[0], Number) else 0

class AgentNaive_Random(IAgent):
    def __init__(self, name="NAIVE", id="0"):
        self.name = "RANDOM_"+name
        self.reward = RewardOnlyWinning()
        self.id = id
        self.exe_path = None
    
    def getAction(self, observations):
        #time.sleep(1)
        itemindex = np.array(np.where(np.array(observations[28:]) == 1))[0].tolist()
        random.shuffle(itemindex)
        a = np.array([1 if i == itemindex[0] else 0 for i in range(200)])
        return a

    def actionUpdate(self, observations, nextobs, action, reward, info):
        pass

    def observeOthers(self, envInfo):
        pass

    def matchUpdate(self, envInfo):
        pass

    def getReward(self, info, stateBefore, stateAfter):
        return self.reward.getReward(info["thisPlayerPosition"], info["thisPlayerFinished"])

class UnityAgent(IAgent):
    def __init__(self, name="HUMAN", id="0"):
        self.name = name
        self.reward = RewardOnlyWinning()
        self.id = id
        self.exe_path = os.path.join("unity_windows9", "ChefsHat.exe")

        self.chosen_move = -1
        self.hand_view = []
        self.valid_moves = []
        self.my_turn = True

        self.info = {}
    
    def updateInfo(self, info: dict):
        jsonified_info = {}
        for k in info.keys():
            if isinstance(info[k], np.ndarray):
                jsonified_info[k] = info[k].tolist()
            elif isinstance(info[k], np.int32):
                jsonified_info[k] = int(info[k])
            else:
                jsonified_info[k] = info[k]
        self.info = jsonified_info

    def getAction(self, observations):
        observations = np.array(observations * 13, dtype=int).tolist()

        self.hand_view = sorted(observations[11:28])
        self.valid_moves = np.argwhere(np.array(observations[28:]) > 0).flatten().tolist()
        self.my_turn = True

        while self.chosen_move < 0:
            pass

        a = np.array([1 if i == self.chosen_move else 0 for i in range(200)])

        self.valid_moves = []
        self.chosen_move = -1
        self.my_turn = False
        
        return a

    def actionUpdate(self, observations, nextobs, action, reward, info):
        self.updateInfo(info)

    def observeOthers(self, envInfo):
        self.updateInfo(envInfo)

    def matchUpdate(self, envInfo):
        self.updateInfo(envInfo)

    def getReward(self, info, stateBefore, stateAfter):
        self.updateInfo(info)