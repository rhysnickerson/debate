from dataclasses import dataclass
from random import normalvariate,  randint, shuffle, choice, random
from math import sqrt
import string
from uuid import uuid4, UUID


K = 32 
D = 400
starting_elo = 1000.0
RATING_FLOOR = 100


#generates a random debater, which is just a normal distribution of their speech, to get a speaker score sample from the distribution
@dataclass
class Debater:
    mean_speak : float   
    variance : float

    def sample_speech(self) -> float:
        return normalvariate(self.mean_speak, sqrt(self.variance))

    @classmethod
    def create_random(cls):
        mean = normalvariate(75, sqrt(5))
        var = random()*5
        return cls(mean, float(var))



#team, composed of two debaters, keeps in tournaments data
@dataclass
class Team:
    debater_a : Debater
    debater_b : Debater

    name : str #uuid used for hashing
    elo : float = starting_elo

    #in tournament data
    speaks : float = 0.0
    score : int = 0
    def reset(self):
        self.speaks = 0
        self.score = 0

    #sample distribution, used to adjudicate round wins
    def round_performance(self) -> float:
        return self.debater_a.sample_speech() + self.debater_b.sample_speech()

    def expected_score(self, teams):
        sum = 0.0
        for team in teams:
            if team == self: continue
            sum += (1/(1+(10**((team.elo - self.elo)/D))))
        return sum
    def update_elo(self, expected_score : float, actual_score : float) -> float:
        self.elo += (K/3)*(actual_score - expected_score)
        self.elo = max(self.elo, RATING_FLOOR)
    
    @staticmethod 
    def random_name():
        return str(uuid4())
    @classmethod
    def create_random(cls, name=""):
        if name == "": name = Team.random_name()
        return cls(Debater.create_random(), Debater.create_random(), name)

    def __str__(self):
        return f"({self.name}): elo:{self.elo}, points:{self.score}, speaks:{self.speaks}"
    def __lt__(self, other):
        if self.score == other.score:
            return self.speaks < other.speaks
        return self.score < other.score
    def __repr__(self):
        return self.name
    #useable because no UUID collisions
    def __hash__(self) -> int:
        return hash(self.name)

class Tournament:
    #generate touurnaments with n rounds, and n_teams, will generate extra teams
    def __init__(self, n_rounds : int, n_teams : int, teams : [Team] = []):
        self.n_rounds = n_rounds
        #pad with swings to have full rounds
        if(n_teams % 4 != 0):
            swings = (4-n_teams%4)
            n_teams += swings
            print(f"Adding {swings} swing teams, now have {n_teams} teams")
            for i in range(swings):
                teams.append(Team.create_random(f"SWING {i+1}"))
        self.n_teams = n_teams 

        self.teams = teams
        if(n_teams > len(self.teams)):
            print(f"Generating {n_teams -len(self.teams)} teams")
            for i in range(n_teams-len(self.teams)):
                self.teams.append(Team.create_random())
        elif(n_teams < len(self.teams)):
            print(f"Teams in tournament exceeds n_teams, culling {len(self.teams)-n_teams}") 
            self.teams = self.teams[:n_teams]
        
        for team in self.teams:
            team.reset()

        self.round_results = []

    #two methods of pairing, random and folding
    #TODO: fix folding, implement tapered scoring
    def simulate(self, method="folding"):
        for i in range(self.n_rounds):
            if method == "random":
                round_result = self.resolve_round_random()
            elif method == "folding":
                round_result = self.resolve_round_folding()
            else:
                raise RuntimeError(f"Unknown pairing method {method}")
            self.round_results.append(round_result)
        self.teams.sort()

    #pair teams randomly
    def resolve_round_random(self):
        results = []
        shuffle(self.teams)
        for i in range(0, self.n_teams, 4):
            room_result = self.resolve_room(self.teams[i:i+4])
            results.append(room_result)
        return results

    #basic bracket folding
    def resolve_round_folding(self):
        #going to use top bracket pullups for now, will do more sophisiticated tournament simulation later
        results = []
        shuffle(self.teams)
        self.teams.sort()
        for i in range(0, self.n_teams, 4):
            room_result = self.resolve_room(self.teams[i:i+4])
            results.append(room_result)
        return results
        
    @staticmethod
    def update_elos(results : {Team : int}):
        for team, actual in results.items():
            expected = team.expected_score(results.keys())
            team.update_elo(expected, actual)

    @staticmethod
    def resolve_room(teams : (Team, Team, Team, Team)):
        scores = [(team.round_performance(),team) for team in teams] 
        i = 0
        round_result = {} 
        for score, team in sorted(scores):
            team.score += i
            team.speaks+= score
            round_result[team] = i
            i+=1
        Tournament.update_elos(round_result)
        return round_result

if __name__ == "__main__":
    #generate 1000 teams
    teams = [Team.create_random() for i in range(1000)]

    #set elos by hosting 200 random tournaments of 100 randomly sampled teams
    for i in range(200):
        shuffle(teams)
        t = Tournament(6, 100, teams[:100])
        t.simulate("folding")


    #host "WUDC" with all teams, print their results
    t = Tournament(6, len(teams), teams)
    t.simulate("folding")
    for team in t.teams:
        print(team)

'''
#for seeing individual round results
i = 1
for round in t.round_results:
    print("Round:", i)
    i+=1
    for room in round:
        print('\t', room)
'''

