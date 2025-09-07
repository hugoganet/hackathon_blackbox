import React, { useState } from 'react';
import { Folder, Plus, FileText, Code, Settings } from 'lucide-react';

interface FileItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  language?: string;
  children?: FileItem[];
}

interface FileExplorerProps {
  onFileSelect: (fileName: string, content: string) => void;
  onNewFile: () => void;
}

const FileExplorer: React.FC<FileExplorerProps> = ({ onFileSelect, onNewFile }) => {
  const [files, setFiles] = useState<FileItem[]>([
    {
      id: '1',
      name: 'main.js',
      type: 'file',
      language: 'javascript'
    },
    {
      id: '2',
      name: 'utils.js',
      type: 'file',
      language: 'javascript'
    },
    {
      id: '3',
      name: 'styles.css',
      type: 'file',
      language: 'css'
    }
  ]);

  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const getFileIcon = (fileName: string, language?: string) => {
    if (language === 'javascript' || fileName.endsWith('.js')) {
      return <Code className="w-4 h-4 text-yellow-500" />;
    }
    if (language === 'css' || fileName.endsWith('.css')) {
      return <Settings className="w-4 h-4 text-blue-500" />;
    }
    return <FileText className="w-4 h-4 text-gray-500" />;
  };

  const handleFileClick = (file: FileItem) => {
    if (file.type === 'file') {
      setSelectedFile(file.id);
      // Generate sample content based on file type
      let content = '';
      if (file.language === 'javascript') {
        content = `// ${file.name}\n\nfunction example() {\n  console.log("Hello from ${file.name}");\n}\n\nexample();`;
      } else if (file.language === 'css') {
        content = `/* ${file.name} */\n\nbody {\n  margin: 0;\n  padding: 20px;\n  font-family: Arial, sans-serif;\n}`;
      }
      onFileSelect(file.name, content);
    }
  };

  const handleNewFile = () => {
    const newFileName = `new-file-${Date.now()}.js`;
    const newFile: FileItem = {
      id: Date.now().toString(),
      name: newFileName,
      type: 'file',
      language: 'javascript'
    };
    setFiles([...files, newFile]);
    onNewFile();
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 border-r border-gray-200">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">Files</h3>
          <button
            onClick={handleNewFile}
            className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
            title="New File"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {files.map((file) => (
            <div
              key={file.id}
              onClick={() => handleFileClick(file)}
              className={`
                flex items-center px-2 py-1 rounded cursor-pointer text-sm
                ${selectedFile === file.id
                  ? 'bg-primary-100 text-primary-900'
                  : 'text-gray-700 hover:bg-gray-100'
                }
              `}
            >
              {file.type === 'folder' ? (
                <Folder className="w-4 h-4 mr-2 text-blue-500" />
              ) : (
                <div className="mr-2">
                  {getFileIcon(file.name, file.language)}
                </div>
              )}
              <span className="truncate">{file.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FileExplorer;
