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

Indentation in EasyDatapacks is either a single tab, or 4 spaces.

## Parameters?!

Normally, functions can only be run as-is and don’t accept any parameters. EasyDatapacks allows you to include entities parameters. (note: the “#p” at the end of the parameter is a clarifier. Ignore it for now, it will be explained later on.)
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

Guess what, functions aren’t functions anymore. They are commands. The /function command is no longer used. With def, you are creating a brand new command which you can use just like vanilla commands. Here’s an example:
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
Else will also match with any other implicit execute statement. The way it works is simple: If the previous block of code is never run, then the else block will run.
```
def example:
    as @e:
        say "Here I am!"
    else:
        tellraw @a “There are no entities.”
```
Else can be used along with other implicit executions, though it must come first.
```
def example:
    as @e[type=!Player]:
        say "Here I am!"
    else as @a:
        say “There are no entities.”
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
actually won’t work. The function will fail to load because you can’t run tellraw on entities. To solve this problem, you need to use clarifiers. A clarifier is a # followed by some letters indicating what you want to clarify. For entities, this can be `p`, to indicate players, or `1`, to indicate a single entity. You can combine both as `#1p` or `#p1`. You write it directly after the variable name, like this:
```
def example1:
    player = @p
    tellraw player#p “hi”
def example2:
    target = @r
    tp @a target#1
```
We had to use `#1` on the target variable because you can only tp to a single entity.

The situation may also arise where you don't want a variable to be replaced with an entity query. For example, say you want to take a player and print their name like this: "[player] emorgan00". However, you want some specific coloring as well:
```
def say_my_name player:
    tellraw @a ["[",{"text":"player", "color":"blue"},"] ",{"selector":"player"}]
```
The "player" variable will be detected twice, although the first one is unintentional. The output will end up looking something like this:
`[@e[...some random stuff...]] emorgan00`
The solution is to use the `#v` clarifier, which tells the compiler to just use the variable name instead of a selector:
```
def say_my_name player:
    tellraw @a ["[",{"text":"player#v", "color":"blue"},"] ",{"selector":"player"}]
```

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
Global = #e
def load:
    Global = summon armor_stand 0 0 0 {CustomName=”\”Global\””}
    scoreboard objectives add timePassed dummy
    scoreboard players set Global timePassed 0
def tick:
    scoreboard players add Global timePassed 1
```
Now, the scope of Global is across the whole program, and it can be accessed anywhere, but we don’t assign an armor stand into it until the load function.

Delayed assignments also work for integer variables, and are used in the same way, just with `#i`.

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

Most programming languages have some sort of `while` loop. EasyDatapacks also implements a while loop, which works just like `if`:
```
def goforward:
    while entity @p:
        say "yep, @p is here"
```
There is also a `whilenot` keyword which works just like `unless`:
```
def goforward:
    whilenot block 0 0 0 stone:
        say "0 0 0 isn't stone"
```
**Warning!** For people who are less experienced with programming, please be very careful when using while/whilenot loops. The loops will automatically be restricted to 65536 calls by Minecraft to prevent crashing, but accidentally producing an infinite loop can still cause extreme lag.

For more complex programs, some users may want the conditionals of while/whilenot loops to use other execute subcommands. For these situations, there is the `loop` command, which is slightly more cumbersome to use but is significantly more powerful. Syntactically, `loop` works just like the `execute` command, but will repeatedly be called until it fails. Here's an example:
```
def movetowall:
    loop at @p if block ~ ~ ~ air:
        tp @p ^ ^ ^0.1
```
You may notice that `while` is simply a shortcut for `loop if`, and `whilenot` is short for `loop unless`. Please also note that the danger posed by `while` is increased in calls to `loop`, as using a selector in a subcommand with multiple entities can cause the loop to fork each call.

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
Two variables can also be compared:
```
def example:
    a = 10
    b = 15
    while a < b:
        a += 1
```

## Integer Clarifiers

There are clarifiers for integer variables just like for entity variables. Integer variables can use the `#v` clarifie, but also have a `#t` clarifier, which stands for "text". Normally an integer variable will evaluate to a selector and score, for use in hybrid scoreboard commands etc. When you want to actually print a score to the chat as part of a JSON array, the syntax is different. Using the `#t` clarifier will cause the variable to be replaced with a JSON component which returns the score as text:
```
def example:
    a = 100
    tellraw @a ["The value of a#v is currently ", a#t]
```
This would cause the following to be printed to chat:
`The value of a is currently 100`

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

Defining a function that takes an integer as a parameter is a little more complicated, as you will need to use clarifiers, since all parameters refer to entities by default. Tagging a parameter with `#i` will cause it to refer to an integer.
```
def speak_n_times n#i:
    while n > 0:
        say "This message will be repeated n times!"
        n -= 1

def example:
    speak_n_times 10
```
For readability purposes, it is recommended that you also tag you entity parameters with `#e`, like this:
```
def greet_n_times player#e n#i:
    while n > 0:
        tellraw player#p "Good morning!"
        n -= 1

def example:
    greet_n_times @r 10
```

## Clarifiers in Parameters

If you know in advance that a parameter will always be a player or a single entity, you may find it simpler to use the corresponding clarifier in the function declaration. EasyDatapacks does in fact support this. For example, the two following functions are equivalent:
```
def greet1 player:
    tellraw player#p "Hello!"
    give player#p bread 1

def greet2 player#p:
    tellraw player "Hello!"
    give player bread 1
```

Please note that the `#p` status of the `player` variable would be overwritten if you were to reassign another entity to the variable. For example, the following would not work:
```
def greet player#p:
    player = @p
    give player bread 1
```

## Variables as JSON Text Components

Suppose you want a function which takes a player as input, and then prints that player's name to the chat. Vanilla commands allow you to convert entity names and scores to test as part of a JSON array, which is what we will need to use to make this work. However, unlike a command parameter, entity selectors appear in JSON as text. Thankfully, EasyDatapacks will also parse any JSON inputs in your program and detect variables or parameters, incorporating them accordingly.

Here is how the above example could be written:
```
def say_my_name someplayer:
    tellraw @a [{"text": "Hi, my name is "}, {"selector":"someplayer"}]

def example:
    say_my_name @p
```
The "someplayer" parameter will be detected and the function will print the input's name as desired. This also works for variables:
```
def example:
    someplayer = @r
    tellraw @a [{"text": "Hi, my name is "}, {"selector":"someplayer"}]
```

## Text Strings

EasyDatapacks has two data types which are used at run-time, but it also has a third data type which is handled only at compile time: Strings.

A string is any piece of raw text which can be inserted into a command at any location. For example, consider the following program:
```
def example:
    my_favorite_food = chicken
```
Because `chicken` isn't a number or entity, it's just a piece of raw text stored in the variable `my_favorite_food`. This raw text can be used anywhere in a command, such as in the following:
```
def example:
    my_favorite_food = chicken
    give @p my_favorite_food 1
```
This would give me 1 piece of chicken.

Strings can be parameters as well. To indicate that a parameter is a string, use the `#s` clarifier, like this:
```
def give_kindly player#p item_a#s item_b#s:

    give player item_a 1
    give player item_b 1

    tellraw player ["Here, take this ", "item_a", " and ", "item_b", "!"]

def load:

    give_kindly @p chicken bread
```
The above program would give me 1 chicken and 1 bread, and then say `Here, take this chicken and bread!`

## Resolving Type Conflicts

Suppose you have the following program:
```
def example:
    x = 10
    y = 15
    z = 20
    tp @p x y z
```
It should be clear that this program isn't going to work, as `x`, `y`, and `z` are all integers, not strings, and you can't teleport a player based on scoreboard scores. In order to resolve this, we will need to let the compiler know that we want to our variables to have the string data type:
```
def example:
    x#s = 10
    y#s = 15
    z#s = 20
    tp @p x y z
```
This will work. In general, if something isn't the data type you want it to be, you can place a clarifier on the variable or parameter name to fix it. If no clarifier is supplied, the compiler will "guess" what data type you are using, but that guess can sometimes be wrong, like in the above example.

For those who may be wondering, the following are all also valid:
```
def example:
    player#p1 = @p
    stand#e = summon armor_stand ~ ~ ~
    number#i = 15
    text#s = @e
```

## Parameter Defaults

Suppose you want to have a function that has an optional argument, called `shout`, which you call in two different ways:
```
shout "Hello"
# prints "Hello!!!!"

shout "Goodbye" blue
# prints "Goodbye!!!!" in blue
```
As you can see, the argument for the color is optional. To create a function like this, we can use parameter defaults. We will have a parameter for our function called `color`, which has a default value of `white` when not provided. Here is what the syntax looks like:
```
def shout message#s color#s=white:
    tellraw @a [{"text":"","color#v":"color"},message,"!!!!"]
```

## Comments

Comments in EasyDatapacks work exactly the same as in normal commands. Just put a "#"" at the beginning of the line, and everything on that line will be ignored. Comments can also be placed at the end of a line. Just enter a space, then a "#", then another space, and everything onwards will be ignored.

## Additional Notes

Currently, any sort of recursion in functions is disallowed due to limitations with data storage in entities. Implementing recursion would introduce a huge amount of complexity to parameter storage, likely leading to immense lag in some cases. In theory, a limited form of recursion could be added without severe drawbacks, but we have opted not to include any recursion as it would likely rarely be used anyway.

Syntactically, one of the most hard-to-get-used-to features introduced by EasyDatapacks is the use of a colon before an indented statement. Because of this, although the use of these colons, especially after "def" statements, is highly recommended for consistency and readability, the following code is completely valid and will be successfully compiled:
```
def function var
    as var
        say Hello
```
Again, some users may find it easier to omit colons for implicit execute statements (such as "as var" above), but this is not considered part of the formal syntax protocol for EasyDatapacks.

# Compiling

EasyDatapacks uses a compiler written in python. The file which you create will be compiled into a set of .json, .mcmeta, and .mcfunction files, which together form a complete datapack. All you need to provide is the destination folder where you want your datapack to reside, and the path to the file(s) which contain the source code for your datapack.

Code on GitHub: https://github.com/emorgan00/EasyDatapacks

## Compiling from the Command Line

First things first, you'll need to install EasyDatapacks:

```sh
$ pip install --user git+https://github.com/emorgan00/EasyDatapacks
```

To use the command line interface, run:

`$ datapack build -o <destination-folder> <input-file>`

This will take the file in `input-file` and compile it into a datapack located at `destination-folder`. Here is an example of what this might look like:

`$ datapack build -o path/to/MyWorld/datapacks/mydatapack path/to/mydatapack.mcf`

If you omit the `-o`, or `--output`, option, the output directory defaults to the name of the first file
without its extension.

Note that I have adopted the .mcf extension for programs in EasyDatapacks, as a shorter version of .mcfunction. I would recommend using the same.

Additionally, you can add one of the following flags:
```
-v, --verbose: print out all generated commands.
-n, --nofiles: don't generate any files.
```
Use a flag like this:

`$ datapack build -v -o <destination-folder> <input-file>`

You can also compile multiple files at once, like this:

`$ datapack build -o <destination-folder> <file1> <file2> <...>`

Compiling multiple files works exactly as if all the code from the separate files was all in one file.

There's also the `link` command, which easily symlinks a given datapack folder into your `.minecraft`
folder, so you can develop it without having to copy it over there every time:

`$ datapack link <datapack-destination-folder> <save-name>`

Every time you update that directory, those updates will also be carried out on the datapack in the
`.minecraft` directory.

# Examples

Here are a few examples of fully working datapacks written with EasyDatapacks:

[String Functions](https://github.com/emorgan00/EasyDatapacks/blob/master/examples/strings.mcf): A brief example of the various things you can do with raw text.

[Raytracing](https://github.com/emorgan00/EasyDatapacks/blob/master/examples/simple_raytracer.mcf): A super simple ray tracing program that shows how simple it is in EasyDatapacks.
