HOW TO ADD A TASK   (everything is in Content/_TASKS)
=====================================================

The game runs the cards in DA_TaskManager from top to bottom.

1. COPY A TEMPLATE
   Open Templates/, pick the one closest to what you want, right-click > Duplicate,
   and drag the copy into Tasks/. Rename it in order, e.g. DA_Task_04_GrabCoffee.
     TEMPLATE_1_TalkToSomeone        walk up to a monster and talk
     TEMPLATE_2_TalkAndSayYes        talk AND pick the reply that gives you work (like "Sure")
     TEMPLATE_3_PickUpItems          pick up some items, done when you have them
     TEMPLATE_4_PickUpAndBringBack   pick up items, then press E at a spot to turn them in
     TEMPLATE_5_GoSomewhere          walk into a spot

2. CHANGE THE WORDS
   Double-click your copy. Everything is under "Task":
     Title          what the clipboard says
     Target         Talk: the monster's name (Boss, Janitor, Floor Manager, Receptionist...)
                    Pick up / Go: a tag you make up, e.g. Task_Coffee
     Count          how many to pick up (0 = all of them)
     DeliverTitle   clipboard text once you have everything (bring-back tasks)
     DeliverTo      tag on the turn-in spot (bring-back tasks)
     DeliverPrompt  words after "Press E", e.g. "to hand over the coffee"
     MeterMonster   whose frustration bar runs during this task (empty = none)
     MeterSeconds   seconds until that bar fills up
     CalmAmount     how much the bar drops when the task is done

3. PUT IT IN THE ORDER
   Open DA_TaskManager, click + on Tasks, and pick your card (or drag it in).
   Drag the rows to change the order.

4. PUT THE STUFF IN THE LEVEL
   Items:     drag BP_TaskPickup into the level (walk into it to pick it up; swap its Mesh
              to whatever the item is). In Details > Actor > Tags add your tag, e.g. Task_Coffee.
              Items stay hidden until their task starts.
   Spots:     drag BP_TaskZone in for a place (an invisible box in game), and give it a tag.
   People:    to turn something in to a monster, select that monster in the level and add the
              tag (e.g. Task_Boss) to its Tags.

EXAMPLE: "Grab the boss a coffee"
   Duplicate TEMPLATE_4_PickUpAndBringBack (it's already filled in for this), put it in Tasks/,
   add it to DA_TaskManager, place a BP_TaskPickup in the break room with tag Task_Coffee,
   and give BP_Monster2 (the Boss) the tag Task_Boss. Done.

OTHER TEXT ON SCREEN
   BP_TaskHUD (Content/TaskSystem) > Class Defaults > HUD Text:
   InteractText ("to interact"), PressWord ("Press"), MemoHeader (clipboard header line).
   Fonts: Font/F_TaskTypewriter (clipboard), Font/F_TaskPrompt (pop-ups).
