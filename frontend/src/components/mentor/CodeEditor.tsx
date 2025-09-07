import React from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  theme?: string;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'javascript',
  theme = 'vs-dark'
}) => {
  const handleEditorChange = (newValue: string | undefined) => {
    onChange(newValue || '');
  };

  return (
    <div className="h-full flex flex-col">
      {/* Editor Header */}
      <div className="bg-gray-800 text-white px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
          <span className="text-sm font-medium ml-4">main.{language === 'typescript' ? 'ts' : 'js'}</span>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={language}
            onChange={(e) => {}}
            className="bg-gray-700 text-white text-sm px-2 py-1 rounded border-none focus:outline-none"
          >
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
          </select>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          language={language}
          theme={theme}
          value={value}
          onChange={handleEditorChange}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            insertSpaces: true,
            wordWrap: 'on',
            contextmenu: true,
            selectOnLineNumbers: true,
            glyphMargin: true,
            folding: true,
            foldingHighlight: true,
            showFoldingControls: 'always',
            smoothScrolling: true,
            cursorBlinking: 'blink',
            cursorSmoothCaretAnimation: true,
            renderLineHighlight: 'line',
            bracketPairColorization: {
              enabled: true
            },
            guides: {
              bracketPairs: true,
              indentation: true
            }
          }}
          loading={
            <div className="flex items-center justify-center h-full bg-gray-900 text-white">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                <p>Loading editor...</p>
              </div>
            </div>
          }
        />
      </div>

      {/* Status Bar */}
      <div className="bg-gray-800 text-gray-300 px-4 py-1 text-xs flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span>Lines: {value.split('\n').length}</span>
          <span>Characters: {value.length}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-green-400">●</span>
          <span>Ready</span>
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;
