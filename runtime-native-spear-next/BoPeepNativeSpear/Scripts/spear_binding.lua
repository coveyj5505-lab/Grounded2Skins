-- Component-relative fit in the actual native spear frame, not a camera offset.
-- Current source crook is root-rigid; +Z is its shaft axis. Native Spear02's
-- current cooked ExtendedBounds confirm +Z is also its long axis.
local M={}
function M.fit(crookMin,crookMax,nativeOrigin,nativeExtent,radialScale)
    radialScale=radialScale or 1.35
    assert(type(radialScale)=='number' and radialScale>=1 and radialScale<=2,'Invalid shaft scale')
    for i=1,3 do
        assert(type(crookMin[i])=='number' and type(crookMax[i])=='number' and crookMax[i]>crookMin[i],'Invalid source bounds')
        assert(type(nativeOrigin[i])=='number' and type(nativeExtent[i])=='number' and nativeExtent[i]>0,'Invalid native bounds')
    end
    assert(nativeExtent[3]>4*math.max(nativeExtent[1],nativeExtent[2]),'Native spear long axis is not Z')
    local height=crookMax[3]-crookMin[3]
    local scale=2*nativeExtent[3]/height
    assert(scale>.5 and scale<2,'Implausible crook/spear length difference')
    local z=nativeOrigin[3]-(crookMax[3]+crookMin[3])*.5*scale
    return {Translation={X=0,Y=0,Z=z},Rotation={X=0,Y=0,Z=0,W=1},Scale3D={X=radialScale,Y=radialScale,Z=scale}}
end
return M
