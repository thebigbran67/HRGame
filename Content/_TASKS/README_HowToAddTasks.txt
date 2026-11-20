HOW TO ADD A TASK   (everything is in Content/_TASKS)
=====================================================

The game runs the cards in DA_TaskManager from top to bottom.
Hover any field on a card to see what it does.

1. COPY A TEMPLATE
   Open Templates/, right-click the closest one > Duplicate, drag the copy into Tasks/,
   and rename it in order, e.g. DA_Task_04_GrabCoffee.
     TEMPLATE_1_TalkToSomeone        walk up to a monster and talk
     TEMPLATE_2_TalkAndSayYes        talk AND pick the reply that takes the job (like "Sure")
     TEMPLATE_3_PickUpItems          pick up some items, done when you have them
     TEMPLATE_4_PickUpAndBringBack   pick up items, then press E at a spot to turn them in
     TEMPLATE_5_GoSomewhere          walk to a place

2. FILL IN THE CARD   (open the Office map first, the pickers only list things in the open map)
   Task Basics
     Title          what the clipboard says
     Type           Talk, Collect or GoTo (type it exactly)
     MustAccept     Talk only: must pick the reply that takes the job
     Count          Collect only: how many items (0 = all of them)
     DeliverTitle   clipboard text once you have everything (bring-back tasks only)
     DeliverPrompt  words after "Press E" at the turn-in spot
   Pick From Level   (dropdown, or click the eyedropper and then click the thing in the level)
     TalkTo         Talk tasks: the monster you talk to
     ItemsToPickUp  Collect tasks: click + once per item, pick each item
     BringItemsTo   bring-back tasks: the dumpster / desk / monster you turn items in at
     GoToPlace      GoTo tasks: the place to walk to (a BP_TaskZone box works great)
     AngryMonster   whose frustration bar fills during this task (empty = no bar)
   Frustration Meter
     MeterSeconds   seconds until the bar fills and you die
     CalmAmount     how much the bar drops when the task is done
   Old Way (typed tags)  only used when the matching picker is empty, you can ignore it

3. PUT IT IN THE ORDER
   Open DA_TaskManager, click + on Tasks, pick your card. Drag rows to reorder.

4. ITEMS AND PLACES IN THE LEVEL
   Items must be pickup objects that disappear when grabbed: drag in BP_TaskPickup
   (walk into it to grab it, swap its Mesh to whatever the item is) or use BP_TrashBag.
   Places: drag in BP_TaskZone (invisible box in game).
   Items for future tasks stay hidden until their task starts.

EXAMPLE: "Grab the boss a coffee"
   Duplicate TEMPLATE_4_PickUpAndBringBack into Tasks/, open it:
     Title "Grab the boss a coffee", Type Collect, DeliverTitle "Bring the coffee to the boss",
     DeliverPrompt "to hand over the coffee", ItemsToPickUp = the coffee BP_TaskPickup you placed,
     BringItemsTo = the Boss, AngryMonster = the Boss.
   Add it to DA_TaskManager. Done.

HOW IT WORKS (if something breaks)
   The Office Level Blueprint (TASK PICKERS box) runs at the start of Play: it finds the
   picked things and gives them a tag like Picked_Items_3, and writes that into the card's
   old typed fields so BP_TaskHUD can read it. When Play stops, the typed fields are put back.
   During Play a card can show Target = Picked_Items_3. That's normal.

OTHER TEXT ON SCREEN
   BP_TaskHUD (Content/TaskSystem) > Class Defaults > HUD Text:
   InteractText ("to interact"), PressWord ("Press"), MemoHeader (clipboard header line).
   Fonts: _TASKS/Font/F_TaskTypewriter (clipboard), F_TaskPrompt (pop-ups).
   Frustration meter + death logic: BP_TaskHUD, red boxes FRUSTRATION METER + KILL and DEATH SCREEN.
