TASK MANAGER  (Content/TaskSystem/TaskManager)
==============================================

The game runs the tasks in DA_TaskManager from top to bottom. The memo in the top-left,
the item counter, the NEW TASK / COMPLETE stamps, the "Press E" prompt and the monster
frustration bar all update by themselves from these cards.

ADD A TASK
1. In Tasks/, right-click a card (DA_Task_...) > Duplicate. Give it a name like DA_Task_04_MakeCoffee.
2. Double-click it and fill in the fields (all under "Task"):
     Title          what the memo says, e.g. "Make the boss some coffee"
     Type           Talk, Collect or GoTo
     Target         Talk    -> the monster's name (Boss, Janitor, Floor Manager, Receptionist Gioh)
                    Collect -> a tag you put on the items, e.g. Task_Coffee
                    GoTo    -> a tag you put on the place, e.g. Task_BreakRoom
     MustAccept     Talk only. Tick it if the task should finish only after the player picks
                    the reply that gives them work (like the janitor's "Sure").
     Count          Collect only. How many items (0 = all of them).
     DeliverTitle   Collect only. Memo text once they have everything, e.g. "Bring the coffee to the boss".
                    Leave empty if the task is done as soon as everything is picked up.
     DeliverTo      Collect only. Tag on the turn-in spot. The player presses E there.
     DeliverPrompt  Collect only. Words after "Press E", e.g. "to hand over the coffee".
     MeterMonster   Name of the monster whose frustration bar runs during this task (empty = no bar).
     MeterSeconds   How long until the bar fills up (and kills the player).
     CalmAmount     How much the bar drops when this task is done.
3. Open DA_TaskManager and drag the card into the Tasks list where you want it in the order.

PUT IT IN THE LEVEL
- Collect: place BP_TaskPickup actors (or any actor you like) and add the tag to each one
  (Details > Actor > Tags). BP_TaskPickup is picked up by walking into it; change its Mesh to
  whatever the item is. Items stay hidden until their task starts.
- Turn-in spot / GoTo: place BP_TaskZone (a box, invisible in game) and give it the tag.
  You can also tag any existing actor (the dumpster drop-off is tagged Task_Dumpster).

ALREADY SET UP
  01 Talk to the boss        (Talk, Boss)
  02 Talk to the janitor     (Talk, Janitor, MustAccept)
  03 Take out the trash      (Collect Task_Trash -> deliver to Task_Dumpster, janitor's bar runs)
When the last task is done, the game shows TempOverScreen like before.
