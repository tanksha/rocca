#!/usr/bin/env python3

# Experiment to communicate with Minetest via Miney.
#
# Requirements:
#
# - Minetest, version 5.5.0
# - Miney, see https://miney.readthedocs.io/en/latest/index.html
#
# Usage:
#
# 1. Run minetest
# 2. Create game with mineysocket enabled
# 3. Run that script
#
# Acknowledgment:
#
# A lot of understanding (especially the end of the script) comes from
# studying https://github.com/MaikePaetzel/minetest-agent

import copy
import time
import miney

# Delay between each test (in second)
test_delay = 1.0
def log_and_wait(msg : str):
    print("============ {} ============".format(msg))
    time.sleep(test_delay)

# Connect Minetest
log_and_wait("Connect to minetest")
mt = miney.Minetest()
print("mt = {}".format(mt))

# We set the time to mid-day
log_and_wait("Set time to mid-day")
print("mt.time_of_day = {}".format(mt.time_of_day))
mt.time_of_day = 0.5
print("mt.time_of_day = {}".format(mt.time_of_day))

# Set Lua interpreter
log_and_wait("Get lua interpreter")
lua = miney.Lua(mt)
print("lua = {}".format(lua))

# Convert Python data into lua string.
#
# List of supported Python constructs (so far):
# - list
#
# List of unsupported Python constructs (so far):
# - set
# - tuple
log_and_wait("Convert python data to lua")
data = ["123", "abc"]
data_dumps = lua.dumps(data)
print("python data = {}".format(data))
print("lua data_dumps = {}".format(data_dumps))

# Run simple lua code
log_and_wait("Invoke minetest lua interpreter to calculate 1+2")
simple_lua_code = "return 1 + 2"
simple_lua_result = lua.run(simple_lua_code)
print("simple_lua_result = {}".format(simple_lua_result))

# Run lua code to trigger play action, inspired from
# minetest-agent/agent/Rob/atomic_actions.py
#
# Additionally here is a list of potentially useful methods from
# https://minetest.org/modbook/lua_api.html
#
# minetest.player_exists(name)
# minetest.get_player_by_name(name)
# minetest.get_objects_inside_radius(pos, radius)
# minetest.find_node_near(pos, radius, nodenames)
# minetest.find_nodes_in_area_under_air(minp, maxp, nodenames)
# minetest.emerge_area(pos1, pos2, [callback], [param])
# minetest.delete_area(pos1, pos2)
# minetest.line_of_sight(pos1, pos2, stepsize)
# minetest.find_path(pos1,pos2,searchdistance,max_jump,max_drop,algorithm)
# minetest.get_inventory(location)
# minetest.dir_to_yaw(dir)
# minetest.yaw_to_dir(yaw)
# minetest.item_drop(itemstack, dropper, pos)
# minetest.item_eat(hp_change, replace_with_item)
# minetest.node_punch(pos, node, puncher, pointed_thing)
# minetest.node_dig(pos, node, digger)
#
# ObjectRef methods:
# - move_to(pos, continuous=false)
# - punch(puncher, time_from_last_punch, tool_capabilities, direction)
# - get_player_name()
# - set_look_vertical(radians)
# - set_look_horizontal(radians)
# - get_velocity(): returns {x=num, y=num, z=num}
# - add_velocity(vel)
# - set_acceleration({x=num, y=num, z=num})
# - get_acceleration(): returns {x=num, y=num, z=num}
# - set_yaw(radians)
# - get_yaw(): returns number in radians
# - set_attach(parent[, bone, position, rotation, forced_visible])
# - get_attach()
# - get_player_control()
#
# In minetest source code:
# - void LocalPlayer::applyControl(float dtime, Environment *env) (look for "control.jump")
# - int LuaLocalPlayer::l_get_control(lua_State *L) (would be nice if we had set_control)

# Chat
log_and_wait("Send chat to minetest")
chat = """
return minetest.chat_send_all(\"Hello Minetest\")
"""
chat_result = lua.run(chat)
print("chat_result = {}".format(chat_result))

# Testing player
player_name = "singleplayer"

# Check that the player exists
log_and_wait("Check that player exists")
player_exists = """
return minetest.player_exists(\"{}\")
""".format(player_name)
player_exists_result = lua.run(player_exists)
print("player_exists = {}".format(player_exists_result))

# Retrieve the name of the player (given its name, hehe)
log_and_wait("Retrieve player name")
player_retrieve_name = """
local player = minetest.get_player_by_name(\"{}\")
return player:get_player_name()
""".format(player_name)
player_retrieve_name_result = lua.run(player_retrieve_name)
print("player_retrieve_name_result = {}".format(player_retrieve_name_result))

# Create lua runner helper using signleplayer
def player_lua_run(code : str, player : str = "singleplayer"):
    get_player_code = "local player = minetest.get_player_by_name(\"{}\")".format(player)
    full_code = get_player_code + "\n" + code
    print("Run lua code:\n\"\"\"\n{}\n\"\"\"".format(full_code))
    return lua.run(full_code)

# Get player position
log_and_wait("Retrieve player position")
get_player_pos_result = player_lua_run("return player:get_pos()")
print("get_player_pos_result = {}".format(get_player_pos_result))

# Move player to a shifted position.  Setting the continuous argument
# of move_to to true does not work for players (as explained in
# https://github.com/minetest/minetest/blob/master/doc/lua_api.txt).
log_and_wait("Move abruptly player to new position")
player_shifted_pos = copy.copy(get_player_pos_result)
player_shifted_pos['x'] += 1
print("player_shifted_pos = {}".format(player_shifted_pos))
move_player_to = "return player:move_to({})".format(lua.dumps(player_shifted_pos))
move_player_to_result = player_lua_run(move_player_to)
print("move_player_to_result = {}".format(move_player_to_result))

# Come back smoothly to its original position
log_and_wait("Move smoothly player to back to previous position")
player_move_back_result = player_lua_run("return player:add_velocity({x=-6.5, y=0, z=0})")
print("player_move_back_result = {}".format(player_move_back_result))

# Jump
log_and_wait("Jump")
player_jump_result = player_lua_run("return player:add_velocity({x=0, y=6.5, z=0})")
print("player_jump_result = {}".format(player_jump_result))

# # Move player to the coordonates of a tree
# tree_pos = {'y': 14.5, 'x': -302.1969909668, 'z': -200.82400512695}
# move_player_to_tree = """
# local player = minetest.get_player_by_name(\"{}\")
# return player:move_to({}, true)
# """.format(player_name, lua.dumps(tree_pos))
# print("move_player_to_tree = {}".format(move_player_to_tree))
# move_player_to_tree_result = lua.run(move_player_to_tree)
# print("get_player_to_tree_result = {}".format(move_player_to_tree_result))

# # Starts mining
# player = "singleplayer"
# lua_mine = """
# local npc = npcf:get_luaentity(\"""" + player + """\")
# local move_obj = npcf.movement.getControl(npc)
# move_obj:mine()
# return true
# """
# mine_result = lua.run(lua_mine)
# print("mine_result = {}".format(mine_result))

# # Stop mining
# lua_stop = """
# move_obj:mine_stop()
# return true
# """
# stop_result = lua.run(lua_stop)
# print("stop_result = {}".format(stop_result))
