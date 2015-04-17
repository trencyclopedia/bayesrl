from thompsonsampagent import ThompsonSampAgent
import numpy as np

class ThompsonSampAgentPOMDP(ThompsonSampAgent):
    def __init__(self, observation_model, dirichlet_param, reward_param, **kwargs):
        super(ThompsonSampAgentPOMDP, self).__init__(dirichlet_param, reward_param, **kwargs)
        self.observation_model = observation_model
        self.reset_belief()
        self.__compute_policy()
	print self.observation_model

    def reset_belief(self):
        #self.belief = np.array([1./self.num_states for _ in range(self.num_states)])
        self.belief = np.zeros((81,))
        self.belief[7*9+1] = 1.0

    def reset(self):
        super(ThompsonSampAgentPOMDP, self).reset()
        self.reset_belief()

    def interact(self, reward, observation, next_state_is_terminal, idx):
        # Handle start of episode.
        if reward is None:
            # Return random action since there is no information.
            next_action = np.random.randint(self.num_actions)
            self.last_action = next_action
            self.__observe(observation)
            return self.last_action

        # Handle completion of episode.
        if next_state_is_terminal:
            # Proceed as normal.
            pass

        belief = np.array(self.belief[:])
        self.__update_belief(self.last_action, observation)
        for last_state,next_state in [(s,s_) for s in range(self.num_states) for s_ in range(self.num_states)]:
            tp = belief[last_state]*self.belief[next_state]
            # Update the reward associated with (s,a,s') if first time.
            #if self.reward[last_state, self.last_action, next_state] == self.reward_param:
            self.reward[last_state, self.last_action, next_state] *= (1-tp)
            self.reward[last_state, self.last_action, next_state] += reward*tp

            # Update set of states reached by playing a.
            self.transition_observations[last_state, self.last_action, next_state] += tp

        # Update transition probabilities after every T steps
        if self.policy_step == self.T:
            self.__compute_policy()

	print(self.belief)
	input(self.last_action, observation)

        # Choose next action according to policy.
        value_table = sum(self.belief[s]*self.value_table[s] for s in range(self.num_states))
        next_action = self._argmax_breaking_ties_randomly(value_table)

        self.policy_step += 1
        self.last_action = next_action

        return self.last_action

    def __compute_policy(self):
        """Compute an optimal T-step policy for the current state."""
        self.policy_step = 0
        self.transition_probs = np.zeros((self.num_states, self.num_actions, self.num_states))
        for s in xrange(self.num_states):
            for a in xrange(self.num_actions):
                self.transition_probs[s,a] = np.random.dirichlet(self.transition_observations[s,a] +\
                                                            self.dirichlet_param, size=1)
        self._value_iteration(self.transition_probs)

    def __update_belief(self,action,observation):
        self.__transition(action)
        self.__observe(observation)

    def __transition(self,action):
        for s in range(self.num_states):
            self.belief[s] = sum(self.transition_probs[s_,action,s]*self.belief[s_] for s_ in range(self.num_states))

    def __observe(self,observation):
        self.belief = [self.belief[s]*self.observation_model[s][observation] for s in range(self.num_states)]
        Z = sum(self.belief)
        self.belief = np.array(self.belief)/float(Z)
