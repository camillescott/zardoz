#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : weapons.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 23.02.2021

import collections
from dataclasses import dataclass, field
from enum import IntEnum, auto

import dice

from ..utils import require_kwargs, reverse_number, d10, d100, Nd10
from .character import Characteristic
from .combat import (CombatAction, CharacteristicBonus, ExtraHitsBonus,
                     FullAutoBurst, SemiAutoBurst, HIT_LOC_TABLE)


class WeaponClass(IntEnum):
    Pistol = auto()
    Basic = auto()
    Heavy = auto()
    Thrown = auto()
    Melee = auto()


class DamageType(IntEnum):
    Energy = auto()
    Impact = auto()
    Rending = auto()
    Explosive = auto()


class WeaponType(IntEnum):
    Las = auto()
    SP = auto()
    Bolt = auto()
    Melta = auto()
    Plasma = auto()
    Flame = auto()
    Primitive = auto()
    Launcher = auto()
    Grenade = auto()
    Missile = auto()
    Exotic = auto()
    Xenos = auto()
    Chain = auto()
    Shock = auto()
    Power = auto()
    Force = auto()
    Ork = auto()


class ShotType(IntEnum):
    Single = auto()
    Semi = auto()
    Full = auto()


class Craftsmanship(IntEnum):
    Poor = 10
    Common = 0
    Good = -10
    Best = -30


class ItemAvailability(IntEnum):
    Ubiquitous = 70
    Abundant = 50
    Plentiful = 30
    Common = 20
    Average = 10
    Scarce = 0
    Rare = -10
    VeryRare = -20
    ExtremelyRare = -30
    NearUnique = -50
    Unique = -70


class ItemScale(IntEnum):
    Negligible = 30
    Trivial = 20
    Minor = 10
    Standard = 0
    Major = - 10
    Signficant = -20
    Vast = -30

    @staticmethod
    def from_quantity(q):
        if q == 1:
            return ItemScale.Negligible
        elif 2 <= q < 9:
            return ItemScale.Trivial
        elif 10 <= q < 30:
            return ItemScale.Minor
        elif 30 <= q < 500:
            return ItemScale.Standard
        elif 500 <= q < 2000:
            return ItemScale.Major
        elif 2000 <= q < 10000:
            return ItemScale.Signficant
        else:
            return ItemScale.Vast


@require_kwargs
@dataclass(frozen=True)
class Item:

    name: str
    availability: ItemAvailability

    def roll_acquisition(self,
                         quantity: int,
                         profit_factor: int,
                         craftsmanship: Craftsmanship = Craftsmanship.Common,
                         modifier: int = 0):

        roll = dice.roll('1d100')
        return int(roll) <= profit_factor + quantity + self.availability + craftsmanship + modifier


@require_kwargs
@dataclass(frozen=True)
class Weapon(Item):

    weapon_class: WeaponClass
    weapon_type: WeaponType
    weapon_range: int
    rof: tuple
    damage_roll: int
    damage_bonus: int
    damage_type: DamageType
    pen: int
    clip: int
    reload_time: float
    mass: float
    special: tuple = field(default_factory=tuple)
    extra: str = ''
    reference: str = ''

    @property
    def pretty_rof(self):
        single = 'S' if self.rof[0] else '-'
        semi = str(self.rof[1]) if self.rof[1] else '-'
        auto = str(self.rof[2]) if self.rof[2] else '-'
        return f'{single}/{semi}/{auto}'


class InstanceMixin:

    def __init__(self, *,
                 craftsmanship: Craftsmanship,
                 quantity: int = 1,
                 **kwargs):
        
        self.craftsmanship = craftsmanship
        self.quantity = quantity
        
        super().__init__(**kwargs)


class DamageRoll:

    def __init__(self, dice, bonus):
        self.bonus = bonus
        self.fury_bonus = 0
        self.dice = dice

    def replace_lowest(self, replacement):
        if min(self.dice) < replacement:
            self.dice[self.dice.index(min(self.dice))] = replacement

    def __int__(self):
        return sum(self.dice) + self.bonus + self.fury_bonus

    def add_fury(self, extra_fury):
        self.fury_bonus += extra_fury

    def add_bonus(self, extra_bonus):
        self.bonus += extra_bonus



class AttackContext:

    def __init__(self, characteristic, test_base, weapon, target_range, actions = [], quiet: bool = True):
        self.characteristic = characteristic
        self.test_base = test_base
        self.weapon = weapon
        self._test_bonus = 0
        self.target_range = target_range
        self.hits_base = 0
        self.hits_extra = 0
        self.actions = actions

        self.attack_roll = 0
        self.attack_degrees = 0

        self.damage = 0
        self.damage_bonus = 0
        self.damage_rolls = []

    def add_test_bonus(self, extra):
        self._test_bonus += extra

    def add_hits(self, extra):
        self.hits_extra += extra

    def add_damage_roll(self, roll):
        self.damage_rolls.append(roll)

    @property
    def test_bonus(self):
        return min(60, self._test_bonus)

    @property
    def test(self):
        return self.test_base + self.test_bonus

    @property
    def hits(self):
        if SemiAutoBurst in self.actions:
            hits_max = self.weapon.rof_semi
        elif FullAutoBurst in self.actions:
            hits_max = self.weapon.rof_auto
        else:
            hits_max = int(self.weapon.rof_single)
        return min(self.hits_base + self.hits_extra, hits_max)

    @property
    def success(self):
        return self.attack_roll <= self.test

    @property
    def total_damage(self):
        return sum((int(roll) for roll in self.damage_rolls))


class WeaponInstance(InstanceMixin):

    def __init__(self, weapon_model: Weapon, *,
                 craftsmanship: Craftsmanship,
                 quantity: int = 1):

        self.weapon_model = weapon_model
        self.test_characteristic = Characteristic.WeaponSkill \
            if self.weapon_model.weapon_class == WeaponClass.Melee \
            else Characteristic.BallisticSkill
        
        super().__init__(craftsmanship=craftsmanship,
                         quantity=quantity)

    def __str__(self):
        return f'<{self.name} {self.damage_roll}d10+{self.damage_bonus} {self.pretty_rof} {self.range}m>'

    @property
    def range(self):
        return self.weapon_model.weapon_range

    @property
    def name(self):
        return self.weapon_model.name

    @property
    def damage_bonus(self):
        return self.weapon_model.damage_bonus

    @property
    def damage_roll(self):
        return self.weapon_model.damage_roll

    @property
    def rof_single(self):
        return self.weapon_model.rof[0]

    @property
    def rof_semi(self):
        return self.weapon_model.rof[1]

    @property
    def pretty_rof(self):
        return self.weapon_model.pretty_rof

    @property
    def rof_auto(self):
        return self.weapon_model.rof[2]

    def _attack(self, char_val, actions=[], target_range: int = 10, quiet: bool = True):

        def _print(*args, **kwargs):
            if not quiet:
                print(*args, **kwargs)

        #
        # Sanitize parameters
        #

        if not isinstance(actions, collections.Sequence):
            actions = set([actions])
        else:
            actions = set(actions)

        assert len(actions) < 3

        if SemiAutoBurst in actions and not self.rof_semi:
            raise ValueError(f'{self.name} does not support semi-auto')
        if FullAutoBurst in actions and not self.rof_auto:
            raise ValueError(f'{self.name} does not support full-auto')
        if target_range / self.range > 4:
            raise ValueError(f'{self.name} cannot fire more than {self.range * 4}m')

        # setup the attack context
        ctx = AttackContext(self.test_characteristic, char_val, self, target_range, actions=actions, quiet=quiet)

        # apply characteristic bonuses
        for action in actions:
            for bonus in action.before_effects:
                bonus(ctx)
                _print(bonus)
        # now we'd apply specials from the weapon itself in the same way

        # figure ranges
        if target_range <= 2:
            # point blank
            _print('Point blank: +30')
            ctx.add_test_bonus(30)
        elif target_range <= (self.range / 2):
            # short range
            ctx.add_test_bonus(10)
            _print('Close: +10')
        elif target_range >= (self.range * 3):
            # extreme range
            ctx.add_test_bonus(-30)
            _print('Extreme: -30')
        elif target_range >= (self.range * 2):
            # long range
            ctx.add_test_bonus(-10)
            _print('Long: -10')
        else:
            _print('Normal range.')

        _print(f'final test: {ctx.test_base} + {ctx.test_bonus}')

        # roll it
        ctx.attack_roll = d100()
        delta = abs(ctx.test - ctx.attack_roll)
        ctx.attack_degrees = delta // 10

        _print(f'rolled {ctx.attack_roll} for {ctx.attack_degrees} degrees')

        # TODO: check jamming and exploding

        if not ctx.success:
            # damage, effective_char, degrees, hits, locations, message
            return 0, ctx.test, ctx.attack_degrees, 0, [], "Failed to hit"
        else:
            ctx.hits_base = 1

        # apply action bonuses
        for action in actions:
            for bonus in action.after_effects:
                bonus(ctx)
                _print(bonus)

        _print(f'hits after bonus: {ctx.hits}')

        # get hit location with reverse_number
        # for multiple hits 

        # roll for damage
        for hit_counter in range(ctx.hits):
            _print(f'roll hit {hit_counter + 1}')

            roll = DamageRoll(Nd10(n=self.damage_roll), self.damage_bonus)

            _print(f'initial damage roll: {roll.dice}')

            # replace lowest with DoS if its lower
            roll.replace_lowest(ctx.attack_degrees)

            _print(f'damage roll after replace: {roll.dice}')

            # TODO: apply weapon special roll bonuses

            ctx.add_damage_roll(roll)
            _print(f'damage before fury: {int(roll)}')

            fury = 10 in roll.dice
            while (fury):
                fury_roll = d100() <= ctx.test

                if fury_roll:
                    fury_damage = d10()

                    _print(f'fury! rolled {fury_damage}')

                    roll.add_fury(fury_damage)
                    fury = fury_damage == 10
                else:
                    fury = False

        _print(f'final damage: {ctx.total_damage}')
                

        locs = HIT_LOC_TABLE.get_location(ctx.attack_roll, ctx.hits)
        return ctx.total_damage, ctx.test, ctx.attack_degrees, ctx.hits, locs, "Hit!"
