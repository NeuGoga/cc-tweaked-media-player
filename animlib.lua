local player = {}

local ok_zlib, zlib = pcall(require, "zlib_decompress")
local ok_b64, base64 = pcall(require, "base64")

if not ok_zlib then error("Missing library: zlib_decompress.lua. Error: " .. tostring(zlib)) end
if not ok_b64 then error("Missing library: base64.lua. Error: " .. tostring(base64)) end

function player.play(master_filename, mon)
    local master_file = fs.open(master_filename, "r")
    if not master_file then print("Master animation file not found: " .. master_filename); return end
    local master_content = master_file.readAll()
    master_file.close()
    
    local master_anim = textutils.unserializeJSON(master_content)
    if not master_anim or not master_anim.header or not master_anim.chunks then
        print("Invalid master animation file format."); return
    end

    local animation_dir = fs.getDir(master_filename)

    local header = master_anim.header
    local time_per_frame = 1 / (header.fps or 10)
    local anim_scale = header.scale or 0.5
    local term_colors = {}; for char, name in pairs(header.palette) do term_colors[char] = colors[name] end
    
    mon = mon or term.current()
    local original_scale = mon.getTextScale(); mon.setTextScale(anim_scale)
    
    local mon_width, mon_height = mon.getSize()
    local anim_width = header.width; local anim_height = header.height

    if mon_width < anim_width or mon_height < anim_height then
        print(string.format("Error: Monitor too small! Anim: %dx%d, Mon: %dx%d", anim_width, anim_height, mon_width, mon_height))
        mon.setTextScale(original_scale); return
    end

    local x_offset = math.floor((mon_width - anim_width) / 2)
    local y_offset = math.floor((mon_height - anim_height) / 2)
    mon.setCursorPos(1, 1); mon.clear()
    
    local frame_buffer = {}
    for y=1, anim_height do frame_buffer[y] = {} end

    for _, chunk_filename in ipairs(master_anim.chunks) do
        print("Loading chunk: " .. chunk_filename)

        local full_chunk_path = fs.combine(animation_dir, chunk_filename)
        local chunk_file = fs.open(full_chunk_path, "rb")
        if not chunk_file then print("  -> Error: Chunk file not found!"); break end
        local base64_content = chunk_file.readAll(); chunk_file.close()
        base64_content = base64_content:gsub("%s", "")
        
        local chunk_data
        local ok, result = pcall(function()
            local compressed_data = base64.decode(base64_content)
            local json_string = zlib.decompress(compressed_data)
            return textutils.unserializeJSON(json_string)
        end)
        
        if not ok or not result or not result.frames then
            print("  -> Error: Failed to decompress/parse chunk!"); break
        end
        chunk_data = result

        for _, frame in ipairs(chunk_data.frames) do
            local start_time = os.clock()
            
            if frame.type == "full" then
                local i = 1
                for y = 1, header.height do
                    for x = 1, header.width do
                        frame_buffer[y][x] = string.sub(frame.bgs, i, i); i = i + 1
                    end
                end
            elseif frame.type == "delta" then
                for _, change in ipairs(frame.changes) do
                    frame_buffer[change.y][change.x] = change.bg
                end
            end

            for y = 1, header.height do
                mon.setCursorPos(1 + x_offset, y + y_offset)
                for x = 1, header.width do
                    mon.setBackgroundColor(term_colors[frame_buffer[y][x]])
                    mon.write(" ")
                end
            end
            
            local sleep_time = time_per_frame - (os.clock() - start_time)
            if sleep_time > 0 then sleep(sleep_time) end
        end
    end

    mon.setTextScale(original_scale)
    mon.setBackgroundColor(colors.black)
    mon.clear()
end

return player