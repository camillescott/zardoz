#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : simulate.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 27.02.2021

from contextlib import contextmanager
import os


from .combat import player_attack, COMBAT_ACTIONS
from .items import ItemAvailability
from .weapons import (WeaponClass, WeaponType, DamageType, Craftsmanship,
                      PlayerWeapon, PlayerWeaponInstance)

def zimulate(args):

    weapon_model = PlayerWeapon(
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

    weapon_instance = PlayerWeaponInstance(weapon_model, craftsmanship=args.craftsmanship)
    combat_actions = [COMBAT_ACTIONS.get(action) for action in args.actions] \
                     if args.actions is not None else []

    results = simulate_attack(weapon_instance, args.ballistic_skill,
                              args.target_range, combat_actions, N=args.n_trials)
    sr = sum(results.damage > 0) / args.n_trials
    maxd = results.damage.max()
    medd = int(results.damage[results['damage'] > 0].median())

    actions_str = ', '.join([action.name for action in combat_actions])
    title = f'{weapon_instance.name} @ {actions_str}: SR={sr:.3f}, Max={maxd}, Med={medd}\n'\
            f'BS={args.ballistic_skill}, Range={args.target_range}, N={args.n_trials:,} '

    if args.plot is not None:
        if args.plot == 'text':
            plot_simulation_plottile(results)
        else:
            plot_simulation_mpl(results, title=title)


def simulate_attack(instance, BS, target_range, actions, N=10000):
    from alive_progress import alive_bar
    import pandas as pd

    damages, tests = [], []
    with alive_bar(N, title=f'{instance}') as bar:
        for _ in range(N):
            dmg, test, _, _, _, _ = player_attack(instance, BS, actions=actions, target_range=target_range)
            damages.append(dmg)
            tests.append(test)
            bar()
    return pd.DataFrame({'damage': damages, 'test': tests})


def plot_simulation_mpl(results_df, title='', filename=None, **kwargs):
    import matplotlib as mpl
    if os.environ['TERM'] == 'xterm-kitty':
        mpl.use('module://zardoz.mpl-kitty')
    else:
        mpl.use('module://zardoz.mpl-sixel')
    import matplotlib.pyplot as plt
    plt.ioff()
    #import ficus
    import seaborn as sns

    #filename=f'BS{BS}_{weapon_instance.name}_R{target_range}_.png'
    sns.set_style('ticks')
    sns.set_context('talk')

    with mpl_dark_mode():
        fig, ax = plt.subplots(figsize=(12,8))
        sns.kdeplot(data=results_df[results_df['damage'] != 0], x='damage', fill=True, ax=ax)
        sns.despine(ax=ax, offset=10)
        ax.set_xlabel('Damage')
        ax.set_title(title)
        plt.show()


def plot_simulation_plottile(results_df, title='', **kwargs):
    import plotille
    print(title)
    print(plotille.histogram(results_df.damage[results_df.damage > 0],
                             X_label='Damage',
                             x_min=0,
                             height=30))


@contextmanager
def mpl_dark_mode(*args, **kwargs):
    import matplotlib.pyplot as plt
    line_color = 'white'
    with plt.rc_context({'font.family': 'monospace', 'text.color': line_color, 'axes.labelcolor': line_color,
                         'xtick.color': line_color, 'ytick.color': line_color,
                         'axes.edgecolor': line_color, 'axes.facecolor': '#000000',
                         'figure.facecolor': '#000000'}):
        yield line_color
