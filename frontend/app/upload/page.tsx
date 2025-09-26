import FileUpload from "../components/FileUpload";

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            Upload FLEx Data
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            Upload your .flextext files to start analyzing and documenting
            linguistic data
          </p>
        </div>

        <FileUpload />

        <div className="mt-12 max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              About FLEx Files
            </h2>
            <div className="prose prose-sm text-gray-600">
              <p>
                FLEx (FieldWorks Language Explorer) files contain interlinear
                glossed text (IGT) data. These files typically have a .flextext
                extension and contain:
              </p>
              <ul className="mt-4 space-y-2">
                <li>• Texts with morphological analysis</li>
                <li>• Word-level and morpheme-level glosses</li>
                <li>• Part-of-speech tags and grammatical information</li>
                <li>• Language metadata and source information</li>
              </ul>
              <p className="mt-4">
                Once uploaded, your data will be processed and stored in our
                graph database, enabling powerful linguistic analysis and search
                capabilities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
