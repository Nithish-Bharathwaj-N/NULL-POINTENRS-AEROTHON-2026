import React from 'react';

export const OuterTwinView: React.FC = React.memo(() => {
  return (
    <div className="w-full h-full bg-[#060911] overflow-hidden flex flex-col font-mono">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          AEROTWIN Ω — 3D OUTER LAYER VIEWPORT (Turbojetdemo.blend)
          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <iframe
        src="/twin/outer.html"
        title="AEROTWIN Ω 3D Outer Layer Engine Viewport"
        className="w-full h-full border-0 outline-none select-none"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
        allowFullScreen
      />
    </div>
  );
});

OuterTwinView.displayName = 'OuterTwinView';
