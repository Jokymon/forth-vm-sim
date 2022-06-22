## Handling Jump target and encoding resolution
### Problem

For resolving jmp and labels, we would like to get the address of a label by getting the current insertion point into the code.

This would work easy, if we just added every new instruction to the code as soon as it is parsed.

The problem here is, that this way all instructions are added before any of the block grammar rules are executed. So any "prefix"-code, for example for a code or word-definition would never have had a chance to do anything before the code lines are added. We need to collect the code first somewhere else temporarily, then let the blocks execute and only then add the code blocks.

### Solution

When assembling a jmp-immediate instruction, we don't include the target-address, but start with including a 4-byte target-index. This index is then resolved once all the labels have been resolved.

#### Effects

One problem of this approach is that we need to search the generated machine code for jmp instructions (hex 0x64). But can't just take any 0x64 as a jmp instruction, since it is also the ASCII code for a 'd'.
The next idea therefore is to somehow mark the jump with special sequence that will hopefully never appear elsewhere :-( I chose 0x64, 0xff, 0xaa whereas the 0xff was chosen because it represents an illegal instruction and 0xaa because it is hopefully a somewhat exotic addition to 0xff. The downside to this is, that we now can only use 65535 jumps (16-bit) in the entire code. Hopefully we will not run out of them ;-)

- The assembled jump instructions still have final 5-byte of total opcode length and will not disturb any other length/position calculations
- There is no need to change anything about the order in which grammar rules are processed; we can still stick with Lark
- We need a third pass to resolve jmp indices to jmp addresses (first one is simple parsing/assembling, second one is label resolution)
- Process for resolution is a little more complex than that for label resolution