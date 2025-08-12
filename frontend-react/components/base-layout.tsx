"use client"

import type React from "react"
import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Briefcase,
  ChevronDown,
  FileText,
  GraduationCap,
  Home,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  TrendingUp,
  User2,
  CheckCircle,
  AlertTriangle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarSeparator,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { useAuth } from "@/hooks/use-auth"
import { FlashMessage } from "@/components/flash-message"
import { cn } from "@/lib/utils"

interface BaseLayoutProps {
  children: React.ReactNode
  title?: string
  showSidebar?: boolean
}

export function BaseLayout({ children, title, showSidebar = true }: BaseLayoutProps) {
  const { user, isAuthenticated, logout } = useAuth()
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navigationItems = [
    {
      title: "Dashboard",
      href: "/",
      icon: LayoutDashboard,
      active: pathname === "/",
    },
    {
      title: "Job Search",
      href: "/search",
      icon: Search,
      active: pathname === "/search",
    },
    {
      title: "Job Tracker",
      href: "/tracker",
      icon: TrendingUp,
      active: pathname === "/tracker",
    },
    {
      title: "Applications",
      href: "/applications",
      icon: FileText,
      active: pathname === "/applications",
    },
  ]

  const guestNavigationItems = [
    {
      title: "Home",
      href: "/",
      icon: Home,
      active: pathname === "/",
    },
  ]

  // Allow tracker page to show sidebar even without auth for testing
  const isTrackerPage = pathname === "/tracker"
  if (!isAuthenticated && showSidebar && !isTrackerPage) {
    return <GuestLayout title={title}>{children}</GuestLayout>
  }

  if (!showSidebar) {
    return <SimpleLayout title={title}>{children}</SimpleLayout>
  }

  // Use appropriate navigation items based on auth status
  const navItems = isAuthenticated ? navigationItems : guestNavigationItems.concat(navigationItems)

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen bg-background">
        <Sidebar className="fixed left-0 top-0 h-screen z-40 hidden md:flex">
          <SidebarHeader>
            <div className="flex items-center gap-2 px-4 py-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
                <Briefcase className="h-4 w-4 text-primary-foreground" />
              </div>
              <div className="font-semibold">AI Job Qualification</div>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Navigation</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navItems.map((item) => (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton asChild isActive={item.active}>
                        <Link href={item.href}>
                          <item.icon className="h-4 w-4" />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
            {isAuthenticated && (
              <>
                <SidebarSeparator />
                <SidebarGroup>
                  <SidebarGroupLabel>Profile</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      <SidebarMenuItem>
                        <SidebarMenuButton asChild>
                          <Link href="/profile">
                            <GraduationCap className="h-4 w-4" />
                            <span>My Profile</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                      <SidebarMenuItem>
                        <SidebarMenuButton asChild>
                          <Link href="/settings">
                            <Settings className="h-4 w-4" />
                            <span>Settings</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              </>
            )}
          </SidebarContent>
          <SidebarFooter>
            <SidebarMenu>
              <SidebarMenuItem>
                {isAuthenticated ? (
                  <UserMenu user={user} onLogout={logout} />
                ) : (
                  <div className="flex flex-col gap-2 p-2">
                    <Button asChild size="sm">
                      <Link href="/auth/login">Login</Link>
                    </Button>
                    <Button asChild variant="outline" size="sm">
                      <Link href="/auth/register">Register</Link>
                    </Button>
                  </div>
                )}
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>
        </Sidebar>

        {/* Mobile navigation */}
        <div className="flex items-center md:hidden fixed top-0 left-0 right-0 z-50 h-14 border-b bg-background px-4">
          <SidebarTrigger />
          <div className="flex items-center gap-2 ml-4">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary">
              <Briefcase className="h-3 w-3 text-primary-foreground" />
            </div>
            <div className="font-semibold text-sm">AI Job Qualification</div>
          </div>
          <div className="ml-auto">
            <UserMenu user={user} onLogout={logout} compact />
          </div>
        </div>

        <div className="flex-1 ml-0 md:ml-64 pt-14 md:pt-0 overflow-y-auto overflow-x-hidden h-screen">
          <main className="w-full max-w-none py-6 md:py-10">
            <div className="px-6 md:px-10">
              <FlashMessage />
              {title && (
                <div className="mb-6">
                  <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
                </div>
              )}
            </div>
            {children}
          </main>
          <Footer />
        </div>
      </div>
    </SidebarProvider>
  )
}

function UserMenu({ user, onLogout, compact = false }: { user: any; onLogout: () => void; compact?: boolean }) {
  if (!user) return null

  const profileCompleted = user?.profile_completed ?? false
  const emailVerified = user?.email_verified ?? false

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className={cn("w-full justify-start", compact && "h-8 w-8 p-0")}>
          <Avatar className="h-6 w-6">
            <AvatarImage src={user.avatar_url || "/placeholder.svg"} alt={user.display_name || user.email} />
            <AvatarFallback>{(user.display_name || user.email || "U").charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          {!compact && (
            <>
              <div className="flex flex-col items-start ml-2">
                <span className="text-sm font-medium">{user.display_name || user.email}</span>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  {emailVerified ? (
                    <>
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      <span>Verified</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-3 w-3 text-amber-500" />
                      <span>Unverified</span>
                    </>
                  )}
                </div>
              </div>
              <ChevronDown className="ml-auto h-4 w-4" />
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="flex items-center justify-between p-2">
          <span className="text-sm font-medium">Profile Completion</span>
          <Badge variant={profileCompleted ? "default" : "secondary"} className="text-xs">
            {profileCompleted ? "Complete" : "Incomplete"}
          </Badge>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile">
            <User2 className="mr-2 h-4 w-4" />
            <span>My Profile</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/settings">
            <Settings className="mr-2 h-4 w-4" />
            <span>Settings</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onLogout} className="text-red-600">
          <LogOut className="mr-2 h-4 w-4" />
          <span>Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function GuestLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
              <Briefcase className="h-4 w-4 text-primary-foreground" />
            </div>
            <Link href="/" className="font-semibold">
              AI Job Qualification System
            </Link>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link href="/auth/login">Login</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/register">Register</Link>
            </Button>
          </div>
        </div>
      </header>
      <main className="container py-6">
        <FlashMessage />
        {title && (
          <div className="mb-6">
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
          </div>
        )}
        {children}
      </main>
      <Footer />
    </div>
  )
}

function SimpleLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <div className="min-h-screen bg-background">
      <main className="container py-6">
        <FlashMessage />
        {title && (
          <div className="mb-6">
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
          </div>
        )}
        {children}
      </main>
      <Footer />
    </div>
  )
}

function Footer() {
  return (
    <footer className="border-t bg-background">
      <div className="container flex h-14 items-center justify-center">
        <p className="text-sm text-muted-foreground">AI Job Qualification Screening System v3.0.0</p>
      </div>
    </footer>
  )
}
