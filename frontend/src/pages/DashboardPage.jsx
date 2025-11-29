                            >
    {/* Status Badge */ }
    < div className = "absolute top-4 right-4" >
    {
        course.status === 'processing' ? (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-50 text-yellow-700 text-xs font-medium">
                <Loader2 size={12} className="animate-spin" /> 处理中
            </span>
        ) : (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-50 text-green-700 text-xs font-medium">
                <CheckCircle2 size={12} /> 已就绪
            </span>
        )
    }
                                </div >

                                <div className="flex items-start justify-between mb-4">
                                    <div className={`p-3 rounded-lg transition-colors ${course.status === 'ready' ? 'bg-blue-50 text-blue-600 group-hover:bg-blue-100' : 'bg-gray-100 text-gray-400'
                                        }`}>
                                        <BookOpen size={24} />
                                    </div>
                                </div>

                                <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-1 pr-16">
                                    {course.title}
                                </h3>
                                <p className="text-sm text-gray-500 line-clamp-2 mb-4 h-10">
                                    {course.description || "暂无描述"}
                                </p>

                                <div className={`flex items-center text-sm font-medium ${course.status === 'ready' ? 'text-blue-600' : 'text-gray-400'
                                    }`}>
                                    {course.status === 'ready' ? (
                                        <>进入学习 <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" /></>
                                    ) : (
                                        <>AI 生成中...</>
                                    )}
                                </div>
                            </Link >
                        ))}
                    </div >
                )}
            </div >
        </div >
    );
}
