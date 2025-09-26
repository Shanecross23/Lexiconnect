"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { DocumentTextIcon } from "@heroicons/react/24/outline";

const navigation = [
  { name: "Home", href: "/" },
  { name: "Upload", href: "/upload" },
  { name: "Demo", href: "/demo" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link href="/" className="flex-shrink-0 flex items-center">
              {/* <DocumentTextIcon className="block h-6 w-6 text-primary-600" /> */}
              <span className="ml-2 text-xl font-bold text-gray-900">
                Lexiconnect
              </span>
            </Link>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const isCurrent = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isCurrent
                        ? "border-primary-500 text-gray-900"
                        : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <Link
              href="/auth/signup"
              className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
