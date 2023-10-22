from ChefsHatGym.Agents import AgentNaive_Random, RemoteAgent, UnityAgent
from ChefsHatGym.Rewards import RewardOnlyWinning
from ChefsHatGym.env import ChefsHatEnv
import gym
import socket
import time
import random
import os

EXTRA_STEPS = 10


class SimpleGame:
    def __init__(
        self,
        playersAgents,
        gameType=ChefsHatEnv.GAMETYPE["MATCHES"],
        gameStopCriteria=10,
        rewardFunction=RewardOnlyWinning,
        verbose=False,
        episodes=1,
        path=r"E:\workspace\ChefsHatCompetition_Alexandre\examples\game_0",
    ):
        assert len(playersAgents) == 4, "The game must have exactly four agents!"
        self.playersAgents = playersAgents
        self.agentNames = [a.name for a in self.playersAgents]
        self.rewards = [r.getReward for r in self.playersAgents]
        """Game parameters"""
        self.gameType = gameType
        self.gameStopCriteria = gameStopCriteria
        self.rewardFunction = rewardFunction if rewardFunction else RewardOnlyWinning
        """Experiment parameters"""
        self.saveDirectory = path
        self.verbose = verbose
        self.saveLog = False
        self.saveDataset = False
        self.episodes = episodes

    def run(self):
        """Setup environment"""
        self.env = gym.make("chefshat-v0")  # starting the game Environment
        self.env.startExperiment(
            rewardFunctions=self.rewards,
            gameType=self.gameType,
            stopCriteria=self.gameStopCriteria,
            playerNames=self.agentNames,
            logDirectory=self.saveDirectory,
            verbose=self.verbose,
            saveDataset=True,
            saveLog=True,
        )
        """Start Environment"""

        current_extra_steps = EXTRA_STEPS

        for _ in range(self.episodes):
            observations = self.env.reset()

            while not self.env.gameFinished:
                currentPlayer = self.playersAgents[self.env.currentPlayer]
                observations = self.env.getObservation()
                action = currentPlayer.getAction(observations)

                info = {"validAction": False}

                while not info["validAction"]:
                    nextobs, reward, isMatchOver, info = self.env.step(action)

                # humans_finished = all([type(self.playersAgents[i]) is not UnityAgent or sum(self.env.playersHand[i]) == 0 for i in range(4)])
                # current_extra_steps = current_extra_steps - 1 if humans_finished else EXTRA_STEPS

                # Observe others
                for p in self.playersAgents:
                    p.observeOthers(info)
                #
                if isMatchOver:
                    for p in self.playersAgents:
                        p.matchUpdate(info)
