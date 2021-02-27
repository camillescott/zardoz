#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : simulate.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 27.02.2021


from .combat import COMBAT_ACTIONS
from .weapons import (WeaponClass, WeaponType, DamageType, Craftsmanship,
                               ItemAvailability, Weapon, WeaponInstance)

def zimulate(args):
    import plotille

    weapon_model = Weapon(
        name=args.name,
        availability=args.availability,
        weapon_class=args.weapon_class,
        weapon_type=args.type,
        weapon_range=args.range,
        rof=(args.rof_single, args.rof_semi, args.rof_auto),
        damage_roll=args.damage_d10,
        damage_bonus=args.damage_bonus,
        damage_type=args.damage_type,
        pen=args.pen,
        clip=args.clip,
        reload_time=args.reload_time,
        mass=args.mass
    )

    weapon_instance = WeaponInstance(weapon_model, craftsmanship=args.craftsmanship)
    combat_actions = [COMBAT_ACTIONS.get(action) for action in args.actions] \
                     if args.actions is not None else []

    results = simulate_attack(weapon_instance, args.ballistic_skill,
                              args.target_range, combat_actions, N=args.n_trials)
    sr = sum(results.damage > 0) / args.n_trials
    maxd = results.damage.max()
    medd = int(results.damage[results['damage'] > 0].median())

    print(f'Median damage: {medd}')
    print(f'Max damage: {maxd}')
    print(f'Success ratio: {sr}')
    print(plotille.histogram(results.damage[results.damage > 0],
                             X_label='Damage',
                             x_min=0,
                             height=30))


def simulate_attack(instance, BS, target_range, actions, N=10000):
    from alive_progress import alive_bar
    import pandas as pd

    damages, tests = [], []
    with alive_bar(N, title=f'{instance}') as bar:
        for _ in range(N):
            dmg, test, _, _, _, _ = instance._attack(BS, actions=actions, target_range=target_range)
            damages.append(dmg)
            tests.append(test)
            bar()
    return pd.DataFrame({'damage': damages, 'test': tests})


def simulate_and_plot(weapon_instance, BS, target_range, actions=[], N=100000):
    import ficus
    import seaborn as sns

    damages = simulate_attack(weapon_instance, BS, target_range, actions, N=N)
    sr = sum(damages.damage > 0) / N
    maxd = damages.damage.max()
    medd = damages.damage[damages['damage'] > 0].median()

    sns.set_style('ticks')
    with ficus.FigureManager(show=True, figsize=(12,8), filename=f'BS{BS}_{weapon_instance.name}_R{target_range}_.png') as (fig, ax):
        sns.kdeplot(data=damages[damages['damage'] != 0], x='damage', fill=True, ax=ax)
        sns.despine(ax=ax, offset=10)
        ax.set_xlabel('Damage')
        ax.set_title(f'{weapon_instance.name}, {[action.name for action in actions]}, BS={BS}, Range={target_range}\nN={N:,} ({sr:4f} SR), Max={maxd}, Med={medd}')
