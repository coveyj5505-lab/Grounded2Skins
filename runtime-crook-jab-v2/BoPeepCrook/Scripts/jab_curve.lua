-- Cosmetic time-based crook motion only. No native animation/gameplay writes.
local M={}
local function smooth(t) t=math.max(0,math.min(1,t));return t*t*(3-2*t) end
local function mix(a,b,t) return a+(b-a)*smooth(t) end
function M.new()
    local self={lastTime=nil,lastAttack=false,phase='carry',start=0,turn=0,thrust=0,fromTurn=0,fromThrust=0}
    function self.reset()
        self.lastTime=nil;self.lastAttack=false;self.phase='carry';self.start=0
        self.turn=0;self.thrust=0;self.fromTurn=0;self.fromThrust=0
    end
    function self.sample(now,attacking,allowed)
        assert(type(now)=='number' and now==now and now>=0 and now<math.huge,'Finite game time required')
        assert(type(attacking)=='boolean','Boolean attack state required')
        if allowed==false or (self.lastTime and now<self.lastTime) then self.reset() end
        self.lastTime=now
        if allowed==false then return 0,0,'carry' end
        if attacking~=self.lastAttack then
            self.fromTurn=self.turn;self.fromThrust=self.thrust;self.start=now
            self.phase=attacking and 'jab' or 'recover';self.lastAttack=attacking
        end
        local elapsed=now-self.start
        if self.phase=='jab' then
            -- One out-and-back cosmetic stroke per native attack window.
            -- The measured native flag lasts about0.9s; never park at maximum
            -- extension for that entire duration as V1 did.
            if elapsed<.10 then
                self.turn=mix(self.fromTurn,1,elapsed/.10)
                self.thrust=mix(self.fromThrust,-.10,elapsed/.10)
            elseif elapsed<.30 then
                self.turn=1;self.thrust=mix(-.10,1,(elapsed-.10)/.20)
            elseif elapsed<.52 then
                self.turn=1;self.thrust=mix(1,0,(elapsed-.30)/.22)
            else self.turn=1;self.thrust=0 end
        elseif self.phase=='recover' then
            self.turn=mix(self.fromTurn,0,elapsed/.16);self.thrust=mix(self.fromThrust,0,elapsed/.16)
            if elapsed>=.16 then self.phase='carry';self.turn=0;self.thrust=0 end
        else self.turn=0;self.thrust=0 end
        return self.turn,self.thrust,self.phase
    end
    return self
end
return M
