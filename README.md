## Overview

EasyDatapacks is a new programming language for Minecraft. It looks a lot like the vanilla Minecraft commands we all know and love, except for a few big changes.

## All in One File

Normally, datapacks are separated across many folders and files. Datapack creators need to keep track of many moving parts, such as the pack.mcmeta file, the files used to tag which functions are run at load time and at every tick, and so on. EasyDatapacks removes all of this hassle, and everything is in one file.

## Defining Functions

Since everything is in one file, we need a way to create separate functions and run them independently. The solution to this is simple: simply use the python-inspired “def” keyword to define an independent function. Here’s an example:
```
def greet:
    say “Hello everyone!"
```

Indentation in EasyDatapacks is always a single tab.

## Parameters?!

Normally, functions can only be run as-is and don’t accept any parameters. EasyDatapacks allows you to include entities (and integers) as parameters. (note: the “#p” at the end of the parameter is a clarifier. Ignore it for now, it will be explained later on.)
```
def greet player:
    tellraw player#p “Hello!”
```
Functions can take as many parameters as you want.
```
def impersonate A B:
    execute as A run tellraw B#p “Hello!”
```
## Calling Functions

Guess what, functions aren’t functions anymore. They are commands. The /function command is no longer used. With def, you are creating a brand new command which you can use just like vanilla commands. The only difference is that your new command only has entities (and integers) as parameters. Here’s an example:
```
def greet player:
    tellraw player#p “Hello!”

def example:
    tellraw @a “Here’s a demonstration of my new command.”
    greet @r
```
The above program will pick a random player and say “Hello!” to them when example is called.

## Getting rid of /execute

The most complicated part of minecraft commands is probably the /execute command. It’s hard to use, lengthy, and can only run a single command. Because it’s so annoying, we’ve just decided to get rid of it. Instead, we use a syntax which looks just like the old /execute, but spans multiple lines and can accept many functions instead of just one. Here’s an example:
```
def greet player:
   tellraw player#p “Hello!”
   give player#p bread 1

def impersonate A B:
    as A:
        greet B
        tellraw B#p “I assure you, I am truly me!”
```
The above program will execute both greet B and tellraw B as A, something which is normally impossible in normal minecraft commands without retyping the execute command for each individual command you want to run. Just like in /execute, parameters can be chained together:
```
def example:
    at @p if block ^ ^ ^1 diamond_ore:
        tellraw @p “Just mine them already!”
```
This is especially useful for execute conditionals, because it introduces a whole new level of control flow into the program:
```
def example:
    if block 0 0 0 diamond_ore:
        tellraw @p “Yay! Diamonds!”
        at @p:
            summon fireworks_rocket ~ ~ ~

        tellraw @p “Here’s something to mine them with”
        give @p iron_pickaxe

    if block 0 0 0 coal_ore:
        tellraw @p “Coal ore :(”
```

## If-Else

Normal minecraft commands already have an if statement, but we need an else to match the if. How this works should be fairly self-explanatory, but here’s the syntax:
```
def example:
    if block 0 0 0 diamond_ore:
        tellraw @p “Yay! Diamonds!”
    else:
        tellraw @p “Maybe another time.”
```
Please note that else only accompanies if. It doesn’t work with unless, and it doesn’t work with chained if statements. Here are some examples of where else would not work:
```
def example1:
    if block 0 0 0 diamond_ore if entity @p:
        tellraw @p “Yay! Diamonds!”
    else:
        tellraw @p “Maybe another time.”
```
(note: this would still compile, but it wouldn’t behave as expected. It would only flip the block check, and not the entity check)
```
def example2:
    as @p if block 0 0 0 diamond_ore:
        tellraw @p “Yay! Diamonds!”
    else:
        tellraw @p “Maybe another time.” 
```
## Entity Variables

Suppose you want a function that chooses a random player, and then gives them a piece of bread and a sword. How would you write this using normal commands?
```
give @r bread 1
give @r iron_sword 1
```
The above program won’t work, because we won’t be choosing the same player every time. The only way to do it would be to use a more complicated system, probably with tags. However, this is a huge inconvenience and we would rather have a simple solution to this problem.

One way you could do it with EasyDatapacks would be to use a function:
```
def bestow_gifts player:
    give player#p bread 1
    give player#p iron_sword 1

def example:
    bestow_gifts @r
```
The above program would work, but it’s still a little too complicated and introduces a whole new function where we don’t need one. Instead, we can use a variable:
```
def example:
    player = @r
    give player#p bread 1
    give player#p iron_sword 1
```
This program will take a random player, and store it in the player variable. Now we can do whatever we want with our randomly chosen player, and know that we will be targeting the same player every time.

The scope of a variable works the same way as it does in normal programming languages.

### Note:

Entity variables can have selectors, just like @e, @p, etc. Just like this:
```
def example:
    player = @r
    tellraw player#p[tag=TheChosenOne] “You are the chosen one!”
```
## Summon-to-Variable Shortcut

Suppose you want to summon an armor stand, and then immediately place it into a variable. You could do the following:
```
def example:
    summon armor_stand ~ ~1 ~ {ShowArms:1,Tags:["TemporaryTag"]}
    specialstand = @e[tag=TemporaryTag]
    tag specialstand remove TemporaryTag
```
However, this is way more complicated than it should be. Instead, you can use a built-in shortcut:
```
def example:
    specialstand = summon armor_stand ~ ~1 ~ {ShowArms:1}
```
The two programs above will do the exact same thing.

## Clarifiers

Some commands require you to supply a selector which only includes players, or which only includes a single entity. Since a variable refers to one or more entities, something like
```
def example:
    player = @p
    tellraw player “hi”
```
actually won’t work. The function will fail to load because you can’t run tellraw on entities. To solve this problem, you need to use clarifiers. A clarifier is a # followed by p, to indicate players, or 1, to indicate a single entity. You can combine both as #1p or #p1. You write it directly after the variable name, like this:
```
def example1:
    player = @p
    tellraw player#p “hi”
def example2:
    target = @r
    tp @a target#1
```
We had to use #1 on the target variable because you can only tp to a single entity.

When using clarifiers combined with selectors, the syntax should be as follows:
```
def example:
    players = @a
    tellraw players#p[distance=100] “hi”
```

## Load and Tick

Most datapacks include two special functions: “load” and “tick”. Normally these are specified in the load.json and tick.json files respectively, but this is too complicated. In an EasyDatapacks program, simply name your function “load” or “tick”, and it will automatically work. Here’s an example:
```
def load:
    tellraw @a “Hello!”

def tick:
    tellraw @a “Tick!”
```
Compiling the above program would produce a fully functioning datapack which prints “Hello!” as soon as it is loaded, and then prints “Tick!” every game tick.

## Delayed Assignments

One important thing to note is that free-floating commands outside of any function are totally ignored and will not be run in the datapack. For example:
```
tellraw @a “This message is never printed.”
def load:
    tellraw @a “Hello!”
```
There is one issue that can arise from this. Suppose you wanted an armor stand named “Global” which stored some special data, and you wanted every function to be able to be able to access that data. You could try to do this:
```
Global = summon armor_stand 0 0 0 {CustomName=”\”Global\””}
def load:
    scoreboard objectives add timePassed dummy
    scoreboard players set Global timePassed 0

def tick:
    scoreboard players add Global timePassed 1
```
However, this wouldn’t work, because the first summon command would never get run, and so Global would refer to nothing. Instead, you could try this:
```
def load:
    Global = summon armor_stand 0 0 0 {CustomName=”\”Global\””}
    scoreboard objectives add timePassed dummy
    scoreboard players set Global timePassed 0

def tick:
    scoreboard players add Global timePassed 1
```
This wouldn’t work either, though, because tick is outside the scope of Global.

The solution to this problem is to use a delayed assignment. This means you can declare a variable without actually storing anything in it, basically saying “here’s the scope of this variable, but I’m saving it for later”. Here’s the syntax:
```   
Global = @
def load:
    Global = summon armor_stand 0 0 0 {CustomName=”\”Global\””}
    scoreboard objectives add timePassed dummy
    scoreboard players set Global timePassed 0
def tick:
    scoreboard players add Global timePassed 1
```
Now, the scope of Global is across the whole program, and it can be accessed anywhere, but we don’t assign an armor stand into it until the load function.

Delayed assignments also work for integer variables, and are used in the same way.

## Repeat Loops

Suppose you want to run one of your functions 5 times. Rather than actually typing out the function call 5 times, just use the repeat command:
```
def choose5randomplayers:
    repeat 5:
        tag @r add Tagged
    as @a[tag=Tagged]:
        say “We are the chosen ones!”
```
note: If you are trying to use a repeat loop which repeats many times, consider using a while loop instead. While loops are more advanced and offer more versatility and features. Repeat is really just a shortcut for when you want something to be run a few times.

## While Loops

Most programming languages have some sort of “while” loop. EasyDatapacks also implements a while loop, which works just like “if”:
```
def movetowall:
    while block ~ ~ ~ air:
        tp @s ^ ^ ^0.1
    tp @s ^ ^ ^-0.1
```
There is also a “whilenot” keyword which works just like “unless”:
```
def movetowall:
    whilenot block ~ ~ ~ stone:
        tp @s ^ ^ ^0.1
    tp @s ^ ^ ^-0.1
```
**Warning!** For people who are less experienced with programming, please be very careful when using while/whilenot loops. It is very easy to accidentally create an infinite loop, which will cause Minecraft to crash!

## Break and Continue

Many programming languages with loops will also have two important keywords: break and continue. EasyDatapacks offers both of these for while and whilenot loops. break will cause a loop to immediately exit, and continue will cause a loop to restart from the beginning. Here is an example of how to use them:
```
def movetowall:
    while entity @s:
        unless block ^ ^ ^0.1 air:
            say “I reached a wall! Time to stop moving!”
            break
        tp @s ^ ^ ^0.1
```

## Integer Variables

The minecraft scoreboard already allows you to work with integer variables, but EasyDatapacks offers several shortcuts for quickly working with ints without having to worry about entities or objectives. Declaring an integer variable works just like declaring a entity variable:
```
def example:
    score = 10
```
The scoreboard also allows you to change variables with augmented assignments, and that is implemented here as well:
```
def example:
    score = 10
    score *= 2
    score /= 10
```
Anything that is available with the /scoreboard operation command is allowed.

Of course, variables can be assigned to other variables, and used to augment other variables:
```
def example:
    a = 10
    b = 20
    a *= b
    b = a
```
Integer variables can also be mixed with scoreboard commands:
```
def example:
    scoreboard objectives add score dummy
    magicnumber = 10
    scoreboard players operation @p score *= magicnumber
    scoreboard players operation magicnumber += @p score
```
Finally, integer variables can be incorporated into if, else, while, and whilenot statements. There are five comparison operators available:

`<, <=, ==, =>, >`

Comparison is always between an integer and a constant, and is done as follows:
```
def example1:
    a = 10
    while a > 0:
        say "this will be repeated 10 times"
        a -= 1

def example2:
    a = 100
    if a == 100:
        say "a is equal to 100"

def example3:
    a = 10
    as @e unless a <= 0:
        say "integer comparisons can also be used in chained execute statements!"
```
The syntax is always: `<variable> <operator> <constant>`

## Integers as Parameters

Integer parameters work exactly as you might expect. When calling a function that has an integer parameter, it looks something like this:
```
def example1:
    speak_n_times 10

def example2:
    b = 10
    speak_n_times b
```
Both of the above are valid.

Defining a function that takes an integer as a parameter is a little more complicated, as you will need to use clarifiers, since all parameters refer to entities by default. Tagging a parameter with #i will cause it to refer to an integer.
```
def speak_n_times n#i:
    while n > 0:
        say "This message will be repeated n times!"
        n -= 1

def example:
    speak_n_times 10
```
For readability purposes, it is recommended that you also tag you entity parameters with #e, like this:
```
def greet_n_times player#e n#i:
    while n > 0:
        tellraw player#p "Good morning!"
        n -= 1

def example:
    greet_n_times @r 10
```

## Comments

Comments in EasyDatapacks work exactly the same as in normal commands. Just put a “#” at the beginning of the line, and everything on that line will be ignored.

# Compiling

EasyDatapacks uses a compiler written in python. The file which you create will be compiled into a set of .json, .mcmeta, and .mcfunction files, which together form a complete datapack. All you need to provide is the destination folder where you want your datapack to reside, and the path to the file(s) which contain the source code for your datapack.

Code on GitHub: https://github.com/emorgan00/EasyDatapacks

## Compiling from the Command Line
**note:** This section will assume you are familiar with using the command line, and running python files.

To use the command line interface, run EasyDatapacks.py:

`$ python EasyDatapacks.py <destination-folder> <input-file>`

This will take the file in <input-file> and compile it into a datapack located at <destination-folder>. Here is an example of what this might look like:

`$ python EasyDatapacks.py path\to\MyWorld\datapacks\mydatapack path\to\mydatapack.mcf`

Note that I have adopted the .mcf extension for programs in EasyDatapacks, as a shorter version of .mcfunction. I would recommend using the same.

Additionally, you can add one of the following flags:
```
-v, -verbose: print out all generated commands.
-n, -nofiles: don't generate any files.
```
Use a flag like this:

`$ python EasyDatapacks.py -v <destination-folder> <input-file>`

You can also compile multiple files at once, like this:

`$ python EasyDatapacks.py <destination-folder> <file1> <file2> <...>`

Compiling multiple files works exactly as if all the code from the separate files was all in one file.

## Compiling with a Python Script
**note:** This section assumes you know how to organize your python files to successfully import a file from EasyDatapacks.

Some users may prefer to use a python script to quickly compile their files. Please note that this uses python 2.7. Once you have the files from EasyDatapacks in the same directory as your script, your code should look something like this:

```
import datapack # this should import datapack.py

destination = “path/to/datapacks/mydatapack”
files = [“path/to/file1.mcf”, “path/to/file2.mcf”]

verbose, nofiles = False, False

datapack.compile(destination, files, verbose, nofiles)
```
# Examples

Here are a few examples of fully working datapacks written with EasyDatapacks. (These were basically thrown together by me, so don’t expect too much in terms of quality)

[hookshot](https://drive.google.com/uc?export=download&id=1hm0vh0N5gg0uQL5E7kludL91BzkHWFfM)
(this will implement a Zelda-like hookshot)

[movingblocks](https://drive.google.com/uc?export=download&id=17TYq3j28m2pqTuK1PMJfxPrSJZn2qFbS)
(this will implement moving blocks which can be pushed along the grid, and slide on ice)
