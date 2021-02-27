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
                     FullAutoBurst, SemiAutoBurst)


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


class InstanceMixin:

    def __init__(self, *,
                 craftsmanship: Craftsmanship,
                 quantity: int = 1,
                 **kwargs):
        
        self.craftsmanship = craftsmanship
        self.quantity = quantity
        
        super().__init__(**kwargs)


class AttackContext:

    def __init__(self, test_base, target_range, actions = [], quiet: bool = True):
        self.test_base = test_base
        self._test_bonus = 0
        self.target_range = target_range
        self.hits_base = 0
        self.extra_hits = 0
        self.actions = actions

        self.attack_roll = 0
        self.attack_degrees = 0

        self.damage = 0
        self.damage_bonus = 0
        self.damage_rolls = []

    def add_test_bonus(self, extra):
        self._test_bonus += extra

    @property
    def test_bonus(self):
        return max(60, self._test_bonus)




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
    def rof_auto(self):
        return self.weapon_model.rof[2]

    def _attack(self, char_val, actions=[], target_range: int = 10, quiet: bool = True):
        ctx = AttackContext(char_val, target_range, quiet=quiet)

        if not isinstance(actions, collections.Sequence):
            actions = [actions]

        assert len(actions) < 3

        if SemiAutoBurst in actions and not semi:
            raise ValueError(f'{self.name} does not support semi-auto')
        if FullAutoBurst in actions and not auto:
            raise ValueError(f'{self.name} does not support full-auto')
        if target_range / self.range > 4:
            raise ValueError(f'{self.name} cannot fire more than {self.range * 4}m')

        test = char_val
        test_bonus = 0

        # apply characteristic bonuses
        # check aim plus inaccurate
        for action in actions:
            for bonus in action.before_effects:
                if isinstance(bonus, CharacteristicBonus) and bonus.characteristic == self.test_characteristic:
                    test_bonus += int(bonus)
                    if not quiet:
                        print(f'add {bonus} for {test}')
        # now we'd apply specials from the weapon itself in the same way

        # figure ranges
        if target_range <= 2:
            # point blank
            test_bonus += 30
        elif target_range < (self.range / 2):
            # short range
            test_bonus += 10
        elif target_range > (self.range * 3):
            # extreme range
            test_bonus -= 30
        elif target_range > (self.range * 2):
            # long range
            test_bonus -= 10

        if not quiet:
            print(f'added range bonus for {test}')

        test_bonus = min(test_bonus, 60)
        test = test + test_bonus
        if not quiet:
            print(f'final bonus: {test}')

        # roll it
        roll = d100()
        delta = abs(test - roll)
        degrees = delta // 10

        if not quiet:
            print(f'rolled {roll} for {degrees} degrees')

        # TODO: check jamming and exploding

        if roll > test:
            # failure
            # damage, effective_char, degrees, hits, locations, message
            return 0, test, degrees, 0, [], "Failed to hit"

        hits = 1

        # apply action bonuses
        for action in actions:
            for bonus in action.after_effects:
                if isinstance(bonus, ExtraHitsBonus):
                    if action is SemiAutoBurst:
                        hits += min(bonus(dos=degrees), semi)
                    if action is FullAutoBurst:
                        hits += min(bonus(dos=degrees), auto)

        if not quiet:
            print(f'hits after bonus: {hits}')

        # get hit location with reverse_number
        # for multiple hits 

        # roll for damage
        damage = 0
        _hits = hits
        while _hits > 0:
            if not quiet:
                print(f'roll hit {_hits}')

            rolls = Nd10(n=self.damage_roll)

            if not quiet:
                print(f'damage rolls: {rolls}')

            # replace lowest with DoS if its lower
            if min(rolls) < degrees:
                rolls[rolls.index(min(rolls))] = degrees

            if not quiet:
                print(f'damage rolls after replace: {rolls}')

            damage += sum(rolls) + self.damage_bonus

            if not quiet:
                print(f'damage before fury: {damage}')

            fury = 10 in rolls
            while (fury):
                fury_roll = d100() <= test

                if not quiet:
                    print(f'fury! rolled {fury_roll}')

                if fury_roll:
                    fury_damage = d10()

                    if not quiet:
                        print(f'fury did {fury_damage}')

                    damage += fury_damage
                    fury = fury_damage == 10
                else:
                    fury = False

            _hits -= 1

        if not quiet:
            print(f'final damage: {damage}')
                

        return damage, test, degrees, hits, [], "Hit!"
