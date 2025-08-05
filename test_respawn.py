#!/usr/bin/env python3
import asyncio
import time
import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from models import Player
from game_state import GameManager

async def test_respawn():
    print("=== Respawn Functionality Test ===")
    gm = GameManager()
    
    # Simulate adding a player to start the game loop
    class MockWebSocket:
        async def send_text(self, text):
            pass
    
    mock_ws = MockWebSocket()
    player = await gm.add_player(mock_ws, "TestPlayer")
    print(f'Player added to game: is_dead={player.is_dead}, respawn_ready={player.respawn_ready}')
    print(f'Game loop started: {gm.game_loop_task is not None}')
    
    # Wait a bit for game loop to run
    await asyncio.sleep(0.1)
    
    # Kill the player
    await gm.kill_player(player)
    print(f'After kill: is_dead={player.is_dead}, respawn_ready={player.respawn_ready}, cooldown={player.respawn_cooldown:.2f}')
    
    # Check timing
    current_time = time.time()
    remaining = player.respawn_cooldown - current_time
    print(f'Current time: {current_time:.2f}, cooldown ends at: {player.respawn_cooldown:.2f}, remaining: {remaining:.2f}s')
    
    # Wait for cooldown to expire (let game loop handle it)
    print('Waiting 3.5 seconds for game loop to handle respawn ready...')
    start_time = time.time()
    
    while time.time() - start_time < 3.5:
        if player.respawn_ready:
            elapsed = time.time() - start_time
            print(f'Player became ready after {elapsed:.2f} seconds!')
            break
        await asyncio.sleep(0.1)
    
    print(f'Current state: is_dead={player.is_dead}, respawn_ready={player.respawn_ready}')
    
    if not player.respawn_ready:
        print("❌ Player never became ready to respawn!")
        return
    
    # Test respawn input handling
    from models import PlayerInput
    respawn_input = PlayerInput(player_id=player.id, action="respawn")
    
    print(f'Testing respawn input...')
    await gm.handle_player_input(respawn_input)
    
    print(f'Final state after respawn input: is_dead={player.is_dead}, respawn_ready={player.respawn_ready}')
    
    if not player.is_dead:
        print("✅ Respawn test PASSED!")
    else:
        print("❌ Respawn test FAILED!")
    
    # Clean up
    if gm.game_loop_task:
        gm.game_loop_task.cancel()
        try:
            await gm.game_loop_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(test_respawn())