const std = @import("std");
const print = std.debug.print;
const ArrayList = std.ArrayList;

fn Icast(T: type, x: anytype) T {
    return @as(T, @intCast(x));
}
fn Fcast(T: type, x: anytype) T {
    return @as(T, @floatCast(x));
}
fn IfromF(T: type, x: anytype) T {
    return @as(T, @intFromFloat(x));
}
fn FfromI(T: type, x: anytype) T {
    return @as(T, @floatFromInt(x));
}

const Move = enum(u8) {
    left,
    right,
    none,
    HALT,

    fn to_val(self: Move) i32 {
        return switch (self) {
            .left => -1,
            .right => 1,
            .none =>  0,
            .HALT =>  0,
        };
    }
};

const PartialInstruction = struct {
    write: bool,
    goto: u32,
    move: Move,
};

const Instruction = struct {
    read0: PartialInstruction,
    read1: PartialInstruction,
};

const Program = struct {
    instr_index: u32 = 0,
    mem_index: i32 = 0,
    instructions: ArrayList(Instruction),
    memory_pos: ArrayList(bool),
    memory_neg: ArrayList(bool),

    fn print_memory(self: Program) void {
        const memory_neg_len = self.memory_neg.items.len;
        for (0..memory_neg_len) |i| {
            if (self.memory_neg.items[memory_neg_len - i - 1]) {
                print("1", .{});
            } else {
                print("0", .{});
            }
        }
        for (self.memory_pos.items) |mem| {
            if (mem) {
                print("1", .{});
            } else {
                print("0", .{});
            }
        }
        print("\n", .{});
        const pointer_pos: usize = Icast(usize, Icast(i32, memory_neg_len) + self.mem_index);
        for (0..pointer_pos) |_| {
            print(" ", .{});
        }
        print("^\n", .{});

    }

    fn print_instructions(self: Program) void {
        const instr_idx_len = std.math.log10_int(self.instructions.items.len);
        for (0..instr_idx_len) |_| {
            print(" ", .{});
        }
        print("      0   |   1  \n", .{});
        for (0..instr_idx_len) |_| {
            print(" ", .{});
        }
        print("    ------+------\n", .{});
        for (self.instructions.items, 0..) |instruction, i| {
            if (i == self.instr_index) { 
                print(">", .{}); 
            } else { 
                print(" ", .{}); 
            }
            const idx_len = if (i != 0) std.math.log10_int(i) else 0;
            for (0..instr_idx_len - idx_len) |_| { 
                print(" ", .{}); 
            }

            print("{d}: ", .{i});
            if (instruction.read0.move == .HALT) {
                print("  HALT  ", .{});
            } else {
                print("{d} {c} {d} ", .{
                    @as(u8, if (instruction.read0.write) 1 else 0),
                    @as(u8, switch (instruction.read0.move) {
                        .left => 'L',
                        .right => 'R',
                        .none => '_',
                        .HALT => 'H',
                    }),
                    instruction.read0.goto,
                });
            }
            if (instruction.read1.move == .HALT) {
                print("| HALT\n", .{});
            } else {
                print("| {d} {c} {d}\n", .{
                    @as(u8, if (instruction.read1.write) 1 else 0),
                    @as(u8, switch (instruction.read1.move) {
                        .left => 'L',
                        .right => 'R',
                        .none => '_',
                        .HALT => 'H',
                    }), 
                    instruction.read1.goto
                });
            }
        }
    }
    
    fn print_state(self: Program) void {
        self.print_memory();
        self.print_instructions();
    }

    fn memory_get(self: Program, mem_idx: i32) bool {
        if (mem_idx < 0) {
            return self.memory_neg.items[Icast(usize, -mem_idx - 1)];
        } else {
            return self.memory_pos.items[Icast(usize, mem_idx)];
        }
    }

    fn memory_set(self: *Program, mem_idx: i32, val: bool) void {
        if (mem_idx < 0) {
            self.memory_neg.items[Icast(usize, -mem_idx - 1)] = val;
        } else {
            self.memory_pos.items[Icast(usize, mem_idx)] = val;
        }
    }

    fn memory_move_index(self: *Program, move: Move) !void {
        self.mem_index += move.to_val();
        // expand memory if needed
        if (self.mem_index < 0) {
            while (self.memory_neg.items.len <= Icast(usize, -self.mem_index)) {
                try self.memory_neg.append(false);
            }
        } else {
            while (self.memory_pos.items.len <= Icast(usize, self.mem_index)) {
                try self.memory_pos.append(false);
            }
        }
    }

    fn run_instruction(self: *Program) !bool {
        const mem_idx = self.mem_index;
        const instr = self.instructions.items[self.instr_index];
        const read_val = self.memory_get(mem_idx);

        var pInstr: PartialInstruction = undefined;
        if (read_val) {
            pInstr = instr.read1;
        } else {
            pInstr = instr.read0;
        }

        if (pInstr.move == .HALT) { return true; }
        self.memory_set(mem_idx, pInstr.write);
        try self.memory_move_index(pInstr.move);
        self.instr_index = pInstr.goto;

        return false;
    }
};


fn parse_program(allocator: std.mem.Allocator, file_path: []const u8) !Program {
    const program_file = try std.fs.cwd().openFile(file_path, .{});
    defer program_file.close();

    var buf: [1024]u8 = undefined;
    var reader = program_file.reader();
    var line_nr: u32 = 0;
    var instruction_list = ArrayList(Instruction).init(allocator);
    var memory_list = ArrayList(bool).init(allocator);
    while (try reader.readUntilDelimiterOrEof(&buf, '\n')) |line| {
        line_nr += 1;

        if (line_nr == 1) {
            for (line) |char| {
                try memory_list.append(char == '1'); 
            }
            continue;
        }

        if (line.len == 0 or line[0] == '#') {
            continue;
        }

        var instruction: Instruction = .{
            .read0 = .{
                .goto = undefined,
                .write = undefined,
                .move = undefined,
            },
            .read1 = .{
                .goto = undefined,
                .write = undefined,
                .move = undefined,
            },
        };
        var instruction_field: u32 = 0;
        var number_str_buf: [10]u8 = undefined;
        var num_buf_index: u32 = 0;
        for (line, 0..) |char, i| {
            if (char == 'H') {
                if (instruction_field == 0) {
                    instruction.read0.move = Move.HALT;
                    continue;

                } else if (instruction_field == 3 or instruction_field == 1) {
                    instruction.read1.move = Move.HALT;
                    instruction_field = 6;
                    break;
                } else {
                    std.log.err("Parse error on line {d}: A HALT instruction can only be the 1., 2. or 4. instruction field, but the {d}. field was read as HALT", .{line_nr, instruction_field+1});
                    return error.ParseError;
                }
            }
            if (char == '#') {
                if (instruction_field != 0 and instruction_field < 6) {
                    std.log.err("Parse error on line {d}: Comment before finishing all instruction fields", .{line_nr});
                    return error.ParseError;
                }
                break;
            } 
            if (char == ' ') {
                if (num_buf_index > 0) {
                    var num = std.fmt.parseInt(u32, number_str_buf[0..num_buf_index], 10) catch |err| {
                        std.log.err("Parse error on line {d}: {s}", .{line_nr, number_str_buf[0..num_buf_index]});
                        return err;
                    };
                    num -= 2;
                    num_buf_index = 0;
                    if (instruction_field == 2) {
                        instruction.read0.goto = num;
                    } else if (instruction_field == 5) {
                        instruction.read1.goto = num;
                    } else {
                        std.log.err("Parse error on line {d}: number was read in instruction field that should be a number", .{line_nr});
                        return error.ParseError;
                    }
                }
                instruction_field += 1;
                continue;
            }
            switch (instruction_field) {
                0 => {
                    switch (char) {
                        '0' => instruction.read0.write = false,
                        '1' => instruction.read0.write = true,
                        else => {
                            std.log.err("Parse error on line {d}: instruction field 0 should be 0 or 1: {s}", .{line_nr, line});
                            return error.ParseError;
                        }
                    }
                },
                3 => {
                    switch (char) {
                        '0' => instruction.read1.write = false,
                        '1' => instruction.read1.write = true,
                        else => {
                            std.log.err("Parse error on line {d}: instruction field 3 should be 0 or 1", .{line_nr});
                            return error.ParseError;
                        }
                    }
                },
                1 => {
                    switch (char) {
                        'L' => instruction.read0.move = Move.left,
                        'R' => instruction.read0.move = Move.right,
                        '_' => instruction.read0.move = Move.none,
                        else => {
                            std.log.err("Parse error on line {d}: instruction field 1 should be L, R, or _", .{line_nr});
                            return error.ParseError;
                        }
                    }
                },
                4 => {
                    switch (char) {
                        'L' => instruction.read1.move = Move.left,
                        'R' => instruction.read1.move = Move.right,
                        '_' => instruction.read1.move = Move.none,
                        else => {
                            std.log.err("Parse error on line {d}: instruction field 4 should be L, R, or _", .{line_nr});
                            return error.ParseError;
                        }
                    }
                },
                2 => {
                    number_str_buf[num_buf_index] = char;
                    num_buf_index += 1;
                },
                5 => {
                    number_str_buf[num_buf_index] = char;
                    num_buf_index += 1;
                    if (i == line.len-1 or line[i+1] == ' ' or line[i+1] == '#') {
                        instruction.read1.goto = std.fmt.parseInt(u32, number_str_buf[0..num_buf_index], 10) catch |err| {
                            std.log.err("Parse error on line {d}: {s}", .{line_nr, number_str_buf[0..num_buf_index]});
                            return err;
                        };
                        instruction.read1.goto -= 2;
                        num_buf_index = 0;
                    }
                },
                else => {
                    std.log.err("Parse error on line {d}: instructions only have 6 fields, {d} were read", .{line_nr, instruction_field+1});
                    return error.ParseError;
                }
            }
        }
        if (instruction_field < 5) {
            std.log.err("Parse error on line {d}: instructions should have 6 fields, {d} were read", .{line_nr, instruction_field+1});
            return error.ParseError;
        }
        try instruction_list.append(instruction);
    }

    return Program{
        .instr_index = 0,
        .mem_index = 0,
        .instructions = instruction_list,
        .memory_pos = memory_list,
        .memory_neg = ArrayList(bool).init(allocator),
    };
}


pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();

    const args = try std.process.argsAlloc(allocator);
    defer std.process.argsFree(allocator, args);
    if (args.len > 2) {
        std.log.err("usage: turing_machine <input_file.tur>", .{});
        return error.ParseError;
    }
    const file_path = if (args.len == 2) args[1] else "main.tur";

    var program = try parse_program(allocator, file_path);
    var halted = false;
    var step: u32 = 0;

    print("--- Initial State ---\n", .{});
    program.print_memory();

    while (!halted) {
        step += 1;
        halted = try program.run_instruction();
        //print("--- Step {d} ---\n", .{step});
        //program.print_memory();
    }
    print("--- Step {d} ---\n", .{step});
    program.print_memory();
}