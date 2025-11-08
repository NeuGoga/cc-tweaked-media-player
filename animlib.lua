local player = {}

local ok_zlib, zlib = pcall(require, "zlib_decompress")
local ok_b64, base64 = pcall(require, "base64")

if not ok_zlib then error("Missing library: zlib_decompress.lua. Error: " .. tostring(zlib)) end
if not ok_b64 then error("Missing library: base64.lua. Error: " .. tostring(base64)) end


function player.play(filename, mon)
    local file = fs.open(filename, "r")
    if not file then
        print("Animation file not found: " .. filename)
        return
    end
    local base64_content = file.readAll()
    file.close()
    
    local anim
    
    local ok, result = pcall(function()
        local compressed_data = base64.decode(base64_content)
        local json_string = zlib.decompress(compressed_data)
        return textutils.unserializeJSON(json_string)
    end)

    if not ok then print("Failed to parse animation file: " .. tostring(result)); return end
    anim = result
    
    local header = anim.header
    local time_per_frame = 1 / header.fps
    local term_colors = {}; for char, name in pairs(header.palette) do term_colors[char] = colors[name] end

    local original_scale = mon.getTextScale()
    mon.setTextScale(header.scale)

    local mon_width, mon_height = mon.getSize()
    local anim_width = header.width
    local anim_height = header.height

    if mon_width < anim_width or mon_height < anim_height then
        print(string.format("Error: Monitor is too small for this scale! Anim: %dx%d, Mon: %dx%d", anim_width, anim_height, mon_width, mon_height))
        mon.setTextScale(original_scale)
        return
    end

    local x_offset = math.floor((mon_width - anim_width) / 2)
    local y_offset = math.floor((mon_height - anim_height) / 2)

    mon = mon or term.current()
    mon.setCursorPos(1, 1)
    mon.clear()

    local frame_buffer = {}
    for y=1, anim_height do frame_buffer[y] = {} end

    for _, frame in ipairs(anim.frames) do
        local start_time = os.clock()
        
        if frame.type == "full" then
            local i = 1
            for y = 1, header.height do
                for x = 1, header.width do
                    frame_buffer[y][x] = string.sub(frame.bgs, i, i)
                    i = i + 1
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
                local color_char = frame_buffer[y][x]
                mon.setBackgroundColor(term_colors[color_char])
                mon.write(" ")
            end
        end
        
        local sleep_time = time_per_frame - (os.clock() - start_time)
        if sleep_time > 0 then sleep(time_per_frame) end
    end

    mon.setTextScale(original_scale)
    mon.setBackgroundColor(colors.black)
    mon.clear()
end

return player