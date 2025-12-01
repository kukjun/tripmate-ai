function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            TripMate AI
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            AI 기반 여행 플래너
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* TODO: Add ChatInterface component */}
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-12 text-center">
          <p className="text-gray-500">
            Phase 1 개발 시작 후 채팅 인터페이스가 추가됩니다.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
