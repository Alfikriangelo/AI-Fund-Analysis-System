'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { documentApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { FileText, CheckCircle, XCircle, Loader2, Upload } from 'lucide-react'

export default function DocumentsPage() {
  const { data: documents, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentApi.list()
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading documents: {(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2">Documents</h1>
          <p className="text-gray-600">
            Manage uploaded fund performance reports
          </p>
        </div>
        <Link
          href="/upload"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
        >
          <Upload className="w-4 h-4" />
          <span>Upload New</span>
        </Link>
      </div>

      {documents && documents.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">No documents uploaded yet.</p>
          <Link
            href="/upload"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Upload Your First Document
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Upload Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fund
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {documents?.map((doc: any) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className="w-5 h-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {doc.file_name}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(doc.upload_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={doc.parsing_status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {doc.fund_id ? `Fund #${doc.fund_id}` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig = {
    completed: {
      icon: <CheckCircle className="w-4 h-4" />,
      text: 'Completed',
      className: 'bg-green-100 text-green-800'
    },
    processing: {
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      text: 'Processing',
      className: 'bg-blue-100 text-blue-800'
    },
    pending: {
      icon: <Loader2 className="w-4 h-4" />,
      text: 'Pending',
      className: 'bg-yellow-100 text-yellow-800'
    },
    failed: {
      icon: <XCircle className="w-4 h-4" />,
      text: 'Failed',
      className: 'bg-red-100 text-red-800'
    }
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending

  return (
    <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.icon}
      <span>{config.text}</span>
    </span>
  )
}
