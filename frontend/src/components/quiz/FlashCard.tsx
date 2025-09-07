import React, { useState } from 'react';
import { QuizCard } from '../../types';
import { CheckCircle, XCircle, RotateCcw, Eye, EyeOff } from 'lucide-react';

interface FlashCardProps {
  card: QuizCard;
  showAnswer: boolean;
  onSubmitAnswer: (selectedAnswer: number) => void;
  onNextCard: () => void;
  disabled?: boolean;
}

const FlashCard: React.FC<FlashCardProps> = ({
  card,
  showAnswer,
  onSubmitAnswer,
  onNextCard,
  disabled = false
}) => {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showHint, setShowHint] = useState(false);

  const handleAnswerSelect = (answerIndex: number) => {
    if (disabled || showAnswer) return;
    setSelectedAnswer(answerIndex);
  };

  const handleSubmit = () => {
    if (selectedAnswer !== null && !disabled) {
      onSubmitAnswer(selectedAnswer);
    }
  };

  const handleNext = () => {
    setSelectedAnswer(null);
    setShowHint(false);
    onNextCard();
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyIcon = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '🟢';
      case 'intermediate': return '🟡';
      case 'advanced': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Card Header */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getDifficultyIcon(card.difficulty)}</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(card.difficulty)}`}>
              {card.difficulty}
            </span>
            {card.programmingLanguage && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                {card.programmingLanguage}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span>Repetitions: {card.repetitions}</span>
            <span>•</span>
            <span>Ease: {card.easeFactor.toFixed(1)}</span>
          </div>
        </div>
        <div className="mt-2">
          <span className="text-sm text-gray-600">{card.topic}</span>
        </div>
      </div>

      {/* Question */}
      <div className="px-6 py-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 leading-relaxed">
          {card.question}
        </h2>

        {/* Answer Options */}
        <div className="space-y-3">
          {card.options.map((option, index) => {
            let optionClass = "w-full p-4 text-left border-2 rounded-lg transition-all duration-200 ";

            if (showAnswer) {
              if (index === card.correctAnswer) {
                optionClass += "border-green-500 bg-green-50 text-green-800";
              } else if (selectedAnswer === index) {
                optionClass += "border-red-500 bg-red-50 text-red-800";
              } else {
                optionClass += "border-gray-200 bg-gray-50 text-gray-500";
              }
            } else {
              if (selectedAnswer === index) {
                optionClass += "border-primary-500 bg-primary-50 text-primary-800";
              } else {
                optionClass += "border-gray-200 hover:border-gray-300 hover:bg-gray-50";
              }
            }

            return (
              <button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                disabled={disabled || showAnswer}
                className={optionClass}
              >
                <div className="flex items-center">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full border-2 border-current flex items-center justify-center mr-3">
                    {showAnswer && index === card.correctAnswer && (
                      <CheckCircle className="w-4 h-4" />
                    )}
                    {showAnswer && selectedAnswer === index && index !== card.correctAnswer && (
                      <XCircle className="w-4 h-4" />
                    )}
                    {!showAnswer && selectedAnswer === index && (
                      <div className="w-2 h-2 bg-current rounded-full"></div>
                    )}
                  </div>
                  <span className="text-sm font-medium">{option}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Hint Toggle */}
        {!showAnswer && (
          <div className="mt-4 text-center">
            <button
              onClick={() => setShowHint(!showHint)}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center mx-auto"
            >
              {showHint ? <EyeOff className="w-4 h-4 mr-1" /> : <Eye className="w-4 h-4 mr-1" />}
              {showHint ? 'Hide Hint' : 'Show Hint'}
            </button>
          </div>
        )}

        {/* Hint */}
        {showHint && !showAnswer && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              💡 <strong>Hint:</strong> Think about the fundamental concepts and best practices for this topic.
            </p>
          </div>
        )}

        {/* Answer Explanation */}
        {showAnswer && (
          <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="flex items-start">
              {selectedAnswer === card.correctAnswer ? (
                <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
              )}
              <div>
                <p className="text-sm font-medium text-gray-900 mb-1">
                  {selectedAnswer === card.correctAnswer ? 'Correct!' : 'Incorrect'}
                </p>
                <p className="text-sm text-gray-700">{card.explanation}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        {!showAnswer ? (
          <button
            onClick={handleSubmit}
            disabled={selectedAnswer === null || disabled}
            className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200"
          >
            Submit Answer
          </button>
        ) : (
          <button
            onClick={handleNext}
            disabled={disabled}
            className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200"
          >
            Next Question
          </button>
        )}
      </div>
    </div>
  );
};

export default FlashCard;
