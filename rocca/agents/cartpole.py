# AUTOGENERATED! DO NOT EDIT! File to edit: 01_cartpole.ipynb (unless otherwise specified).

__all__ = ["FixedCartPoleAgent", "LearningCartPoleAgent"]

# Cell

import gym
import time
import logging

from typing import List

# OpenCog
from opencog.logger import log
from opencog.pln import *
from opencog.type_constructors import *
from opencog.utilities import set_default_atomspace

# ROCCA
from ..envs.wrappers import GymWrapper, CartPoleWrapper
from . import OpencogAgent
from .utils import *

from ..utils import *
from .core import logger as ac_logger

# Cell


class FixedCartPoleAgent(OpencogAgent):
    def __init__(self, env: CartPoleWrapper, atomspace: AtomSpace):
        set_default_atomspace(atomspace)

        # Create Action Space. The set of allowed actions an agent can take.
        # TODO take care of action parameters.
        action_space = {ExecutionLink(SchemaNode(a)) for a in env.action_names}

        # Create Goal
        pgoal = EvaluationLink(PredicateNode("Reward"), NumberNode("1"))
        ngoal = EvaluationLink(PredicateNode("Reward"), NumberNode("0"))

        # Call super ctor
        super().__init__(env, atomspace, action_space, pgoal, ngoal)

    def plan(self, goal, expiry) -> List:
        """Plan the next actions given a goal and its expiry time offset

        Return a python list of cognitive schematics.  Whole cognitive
        schematics are output (instead of action plans) in order to
        make a decision based on their truth values.  Alternatively it
        could return a pair (action plan, tv), where tv has been
        evaluated to take into account the truth value of the context
        as well (which would differ from the truth value of rule in
        case the context is uncertain).

        The format for a cognitive schematic is as follows

        BackPredictiveImplicationScope <tv>
          <vardecl>
          <expiry>
          And (or SimultaneousAnd?)
            <context>
            Execution
              <action>
              <input> [optional]
              <output> [optional]
          <goal>

        """

        # For now we provide 2 hardwired rules
        #
        # 1. Push cart to the left (0) if angle is negative
        # 2. Push cart to the right (1) if angle is positive
        #
        # with some arbitrary truth value (stv 0.9, 0.1)
        angle = VariableNode("$angle")
        numt = TypeNode("NumberNode")
        time_offset = to_nat(1)
        pole_angle = PredicateNode("Pole Angle")
        go_right = SchemaNode("Go Right")
        go_left = SchemaNode("Go Left")
        reward = PredicateNode("Reward")
        epsilon = NumberNode("0.01")
        mepsilon = NumberNode("-0.01")
        unit = NumberNode("1")
        hTV = TruthValue(0.9, 0.1)  # High TV
        lTV = TruthValue(0.1, 0.1)  # Low TV

        # BackPredictiveImplicationScope <high TV>
        #   TypedVariable
        #     Variable "$angle"
        #     Type "NumberNode"
        #   Time "1"
        #   And
        #     Evaluation
        #       Predicate "Pole Angle"
        #       Variable "$angle"
        #     GreaterThan
        #       Variable "$angle"
        #       0
        #     Execution
        #       Schema "Go Right"
        #   Evaluation
        #     Predicate "Reward"
        #     Number "1"
        cs_rr = BackPredictiveImplicationScopeLink(
            TypedVariableLink(angle, numt),
            time_offset,
            AndLink(
                # Context
                EvaluationLink(pole_angle, angle),
                GreaterThanLink(angle, epsilon),
                # Action
                ExecutionLink(go_right),
            ),
            # Goal
            EvaluationLink(reward, unit),
            # TV
            tv=hTV,
        )

        # BackPredictiveImplicationScope <high TV>
        #   TypedVariable
        #     Variable "$angle"
        #     Type "NumberNode"
        #   Time "1"
        #   And
        #     Evaluation
        #       Predicate "Pole Angle"
        #       Variable "$angle"
        #     GreaterThan
        #       0
        #       Variable "$angle"
        #     Execution
        #       Schema "Go Left"
        #   Evaluation
        #     Predicate "Reward"
        #     Number "1"
        cs_ll = BackPredictiveImplicationScopeLink(
            TypedVariableLink(angle, numt),
            time_offset,
            AndLink(
                # Context
                EvaluationLink(pole_angle, angle),
                GreaterThanLink(mepsilon, angle),
                # Action
                ExecutionLink(go_left),
            ),
            # Goal
            EvaluationLink(reward, unit),
            # TV
            tv=hTV,
        )

        # To cover all possibilities we shouldn't forget the complementary
        # actions, i.e. going left when the pole is falling to the right
        # and such, which should make the situation worse.

        # BackPredictiveImplicationScope <low TV>
        #   TypedVariable
        #     Variable "$angle"
        #     Type "NumberNode"
        #   Time "1"
        #   And (or SimultaneousAnd?)
        #     Evaluation
        #       Predicate "Pole Angle"
        #       Variable "$angle"
        #     GreaterThan
        #       Variable "$angle"
        #       0
        #     Execution
        #       Schema "Go Left"
        #   Evaluation
        #     Predicate "Reward"
        #     Number "1"
        cs_rl = BackPredictiveImplicationScopeLink(
            TypedVariableLink(angle, numt),
            time_offset,
            AndLink(
                # Context
                EvaluationLink(pole_angle, angle),
                GreaterThanLink(angle, epsilon),
                # Action
                ExecutionLink(go_left),
            ),
            # Goal
            EvaluationLink(reward, unit),
            # TV
            tv=lTV,
        )

        # BackPredictiveImplicationScope <low TV>
        #   TypedVariable
        #     Variable "$angle"
        #     Type "NumberNode"
        #   Time "1"
        #   And (or SimultaneousAnd?)
        #     Evaluation
        #       Predicate "Pole Angle"
        #       Variable "$angle"
        #     GreaterThan
        #       0
        #       Variable "$angle"
        #     Execution
        #       Schema "Go Right"
        #   Evaluation
        #     Predicate "Reward"
        #     Number "1"
        cs_lr = BackPredictiveImplicationScopeLink(
            TypedVariableLink(angle, numt),
            time_offset,
            AndLink(
                # Context
                EvaluationLink(pole_angle, angle),
                GreaterThanLink(mepsilon, angle),
                # Action
                ExecutionLink(go_right),
            ),
            # Goal
            EvaluationLink(reward, unit),
            # TV
            tv=lTV,
        )

        # Ideally we want to return only relevant cognitive schematics
        # (i.e. with contexts probabilistically currently true) for
        # now however we return everything and let to the deduction
        # process deal with it, as it should be able to.
        return [cs_ll, cs_rr, cs_rl, cs_lr]


# Cell


class LearningCartPoleAgent(OpencogAgent):
    def __init__(self, env: CartPoleWrapper, atomspace: AtomSpace, log_level="debug"):
        set_default_atomspace(atomspace)

        # Create Action Space. The set of allowed actions an agent can take.
        # TODO take care of action parameters.
        action_space = {ExecutionLink(SchemaNode(a)) for a in env.action_names}

        # Create Goal
        pgoal = EvaluationLink(PredicateNode("Reward"), NumberNode("1"))
        ngoal = EvaluationLink(PredicateNode("Reward"), NumberNode("0"))

        # Call super ctor
        super().__init__(
            env, atomspace, action_space, pgoal, ngoal, log_level=log_level
        )

        # Overwrite some OpencogAgent parameters
        self.monoaction_general_succeedent_mining = False
        self.polyaction_mining = False
        self.temporal_deduction = False
