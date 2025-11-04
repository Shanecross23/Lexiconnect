"use client";

interface CorpusStatisticsProps {
  stats: {
    total_texts?: number;
    annotated_texts?: number;
    total_sections?: number;
    total_phrases?: number;
    total_sentences?: number;
    total_words?: number;
    words_by_whitespace?: number;
    words_with_morphemes?: number;
    words_with_only_translation?: number;
    total_morphemes?: number;
    languages?: string[];
    morpheme_types?: Record<string, number>;
    pos_tags?: string[];
  };
}

export default function CorpusStatistics({ stats }: CorpusStatisticsProps) {
  const {
    total_texts = 0,
    annotated_texts = 0,
    total_sections = 0,
    total_sentences = 0,
    total_phrases = 0,
    total_words = 0,
    words_by_whitespace = 0,
    words_with_morphemes = 0,
    words_with_only_translation = 0,
    total_morphemes = 0,
    languages = [],
    morpheme_types = {},
    pos_tags = [],
  } = stats;

  const sentences = total_sentences || total_phrases;

  // Calculate percentages
  const annotationRate =
    total_texts > 0 ? ((annotated_texts / total_texts) * 100).toFixed(1) : "0";
  const wordsWithMorphemesRate =
    total_words > 0
      ? ((words_with_morphemes / total_words) * 100).toFixed(1)
      : "0";
  const wordsWithOnlyTranslationRate =
    total_words > 0
      ? ((words_with_only_translation / total_words) * 100).toFixed(1)
      : "0";

  const statCards = [
    {
      title: "Texts",
      value: total_texts,
      subtitle: `${annotated_texts} annotated (${annotationRate}%)`,
      icon: (
        <svg
          className="w-6 h-6"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      color: "bg-blue-100 text-blue-700",
    },
    {
      title: "Sentences",
      value: sentences,
      subtitle: `${total_sections} sections`,
      icon: (
        <svg
          className="w-6 h-6"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
      ),
      color: "bg-purple-100 text-purple-700",
    },
    {
      title: "Words",
      value: total_words,
      subtitle: `${words_by_whitespace} by whitespace`,
      icon: (
        <svg
          className="w-6 h-6"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
      ),
      color: "bg-green-100 text-green-700",
    },
    {
      title: "Morphemes",
      value: total_morphemes,
      subtitle: `${words_with_morphemes} words have morphemes (${wordsWithMorphemesRate}%)`,
      icon: (
        <svg
          className="w-6 h-6"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      color: "bg-amber-100 text-amber-700",
    },
  ];

  return (
    <div className="w-full space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-stone-950 mb-2">
          Corpus Statistics
        </h2>
        <p className="text-sm text-stone-700">
          Grounding information about your uploaded data
        </p>
      </div>

      {/* Main Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-6 border border-stone-200 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${card.color}`}>{card.icon}</div>
            </div>
            <div>
              <p className="text-3xl font-bold text-stone-950 mb-1">
                {card.value.toLocaleString()}
              </p>
              <p className="text-sm font-semibold text-stone-700 mb-1">
                {card.title}
              </p>
              <p className="text-xs text-stone-600">{card.subtitle}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Annotation Quality Metrics */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-stone-200">
        <h3 className="text-lg font-semibold text-stone-950 mb-4">
          Annotation Quality
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-green-800">
                Words with Morphemes
              </span>
              <span className="text-lg font-bold text-green-900">
                {words_with_morphemes}
              </span>
            </div>
            <div className="w-full bg-green-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all"
                style={{ width: `${wordsWithMorphemesRate}%` }}
              />
            </div>
            <p className="text-xs text-green-700 mt-1">
              {wordsWithMorphemesRate}% of words
            </p>
          </div>

          <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-yellow-800">
                Words with Only Translation
              </span>
              <span className="text-lg font-bold text-yellow-900">
                {words_with_only_translation}
              </span>
            </div>
            <div className="w-full bg-yellow-200 rounded-full h-2">
              <div
                className="bg-yellow-600 h-2 rounded-full transition-all"
                style={{ width: `${wordsWithOnlyTranslationRate}%` }}
              />
            </div>
            <p className="text-xs text-yellow-700 mt-1">
              {wordsWithOnlyTranslationRate}% of words
            </p>
          </div>

          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-800">
                Annotated Texts
              </span>
              <span className="text-lg font-bold text-blue-900">
                {annotated_texts}
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${annotationRate}%` }}
              />
            </div>
            <p className="text-xs text-blue-700 mt-1">
              {annotationRate}% of texts
            </p>
          </div>
        </div>
      </div>

      {/* Additional Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Languages */}
        {languages.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 border border-stone-200">
            <h3 className="text-lg font-semibold text-stone-950 mb-4">
              Languages
            </h3>
            <div className="flex flex-wrap gap-2">
              {languages.map((lang, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-stone-100 text-stone-700 rounded-full text-sm font-medium"
                >
                  {lang}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Morpheme Types */}
        {Object.keys(morpheme_types).length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 border border-stone-200">
            <h3 className="text-lg font-semibold text-stone-950 mb-4">
              Morpheme Types
            </h3>
            <div className="space-y-2">
              {Object.entries(morpheme_types)
                .sort((a, b) => b[1] - a[1])
                .map(([type, count]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between p-2 bg-stone-50 rounded"
                  >
                    <span className="text-sm font-medium text-stone-700 capitalize">
                      {type}
                    </span>
                    <span className="text-sm font-bold text-stone-900">
                      {count}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* POS Tags */}
      {pos_tags.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-stone-200">
          <h3 className="text-lg font-semibold text-stone-950 mb-4">
            Part of Speech Tags ({pos_tags.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {pos_tags.map((tag, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

