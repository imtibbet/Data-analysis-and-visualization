Select 
CONCAT(p2.first, " ", p2.last) AS Pitcher, 
ab.pitcher AS PitcherID,
CONCAT(p1.first, " ", p1.last) AS Batter, 
ab.batter AS BatterID,
ab.stand as hitside,
g.game_id as game_id,
ab.ab_id as ab_id,
p.pitch_id as pitch_id,

p.des, 
ab.des as result,
p.pitch_type,
p.type as called,

p.start_speed,
p.end_speed,

p.sz_top,
p.sz_bot,

p.pfx_x as xmove,
p.pfx_z as zmove,
p.break_length,

p.px as xend,
p.pz as zend,
0 as yend,

p.x0 as xstart,
p.y0 as ystart,
p.z0 as zstart, 

p.vx0 as xvel,
p.vy0 as yvel,
p.vz0 as zvel,

p.ax as xacc,
p.ay as yacc,
p.az as zacc



From games g
LEFT JOIN atbats ab
ON g.game_id = ab.game_id
LEFT JOIN pitches p 
ON p.ab_id = ab.ab_id
JOIN Players p1
ON batter = p1.eliasid
JOIN Players_Copy p2
ON pitcher = p2.eliasid
WHERE SUBSTR(g.date, 1,4) = 2014 
AND ab.pitcher = "433587" 
LIMIT 1000