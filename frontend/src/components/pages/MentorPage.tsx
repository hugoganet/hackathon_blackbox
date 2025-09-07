import React, { useState, useRef } from 'react';
import CodeEditor from '../mentor/CodeEditor';
import ChatPanel from '../mentor/ChatPanel';
import FileExplorer from '../mentor/FileExplorer';

const MentorPage: React.FC = () => {
  const [code, setCode] = useState<string>('function hello() {\n  console.log("Hello, World!");\n}\n\nhello();');
  const [selectedFile, setSelectedFile] = useState<string>('main.js');
  const [panelSizes, setPanelSizes] = useState({ left: 25, middle: 50, right: 25 });
  const [isResizing, setIsResizing] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleFileSelect = (fileName: string, content: string) => {
    setSelectedFile(fileName);
    setCode(content);
  };

  const handleNewFile = () => {
    const newFileName = `new-file-${Date.now()}.js`;
    const newContent = `// ${newFileName}\n\nfunction example() {\n  console.log("Hello from ${newFileName}");\n}\n\nexample();`;
    setSelectedFile(newFileName);
    setCode(newContent);
  };

  const handleMouseDown = (panel: string) => (e: React.MouseEvent) => {
    setIsResizing(panel);
    e.preventDefault();
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isResizing || !containerRef.current) return;

    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = (x / rect.width) * 100;

    if (isResizing === 'left') {
      const newLeft = Math.max(15, Math.min(40, percentage));
      const remaining = 100 - newLeft;
      const middleRatio = panelSizes.middle / (panelSizes.middle + panelSizes.right);
      const newMiddle = remaining * middleRatio;
      const newRight = remaining - newMiddle;
      setPanelSizes({ left: newLeft, middle: newMiddle, right: newRight });
    } else if (isResizing === 'middle') {
      const leftWidth = panelSizes.left;
      const rightStart = leftWidth + panelSizes.middle;
      const newMiddle = Math.max(30, Math.min(70, percentage - leftWidth));
      const newRight = 100 - leftWidth - newMiddle;
      if (newRight >= 20) {
        setPanelSizes({ ...panelSizes, middle: newMiddle, right: newRight });
      }
    }
  };

  const handleMouseUp = () => {
    setIsResizing(null);
  };

  return (
    <div
      ref={containerRef}
      className="h-screen flex bg-gray-50 relative select-none"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* File Explorer - Left Side */}
      <div
        className="min-w-0 bg-white border-r border-gray-200"
        style={{ width: `${panelSizes.left}%` }}
      >
        <FileExplorer onFileSelect={handleFileSelect} onNewFile={handleNewFile} />
      </div>

      {/* Resize Handle - Left */}
      <div
        className="w-1 bg-gray-300 hover:bg-primary-400 cursor-col-resize transition-colors"
        onMouseDown={handleMouseDown('left')}
      />

      {/* Code Editor - Middle */}
      <div
        className="min-w-0 bg-white"
        style={{ width: `${panelSizes.middle}%` }}
      >
        <CodeEditor
          value={code}
          onChange={setCode}
          language="javascript"
        />
      </div>

      {/* Resize Handle - Middle */}
      <div
        className="w-1 bg-gray-300 hover:bg-primary-400 cursor-col-resize transition-colors"
        onMouseDown={handleMouseDown('middle')}
      />

      {/* Chat Panel - Right Side */}
      <div
        className="min-w-0 border-l border-gray-200 bg-white"
        style={{ width: `${panelSizes.right}%` }}
      >
        <ChatPanel code={code} />
      </div>
    </div>
  );
};

export default MentorPage;
