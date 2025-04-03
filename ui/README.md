This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Project Structure

```
ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx             # Root layout
│   │   ├── globals.css            # Global styles (Tailwind imports)
│   │   ├── login/
│   │   │   └── page.tsx           # Login page component
│   │   └── chat/
│   │       └── page.tsx           # Chat page component
│   ├── components/
│   │   ├── ui/                    # Shadcn UI components (auto-generated)
│   │   ├── ChatHeader.tsx         # Chat header component
│   │   ├── ChatItem.tsx           # Individual chat item in the list
│   │   ├── ChatList.tsx           # List of chats in the sidebar
│   │   ├── MessageArea.tsx        # Area displaying messages
│   │   ├── MessageBubble.tsx      # Individual message bubble
│   │   ├── MessageInput.tsx       # Message input footer
│   │   └── Sidebar.tsx            # Main sidebar component
│   ├── lib/
│   │   └── utils.ts               # Shadcn utils (auto-generated)
│   └── store/
│       ├── userStore.ts           # Zustand store for user state
│       └── chatStore.ts           # Zustand store for chat state
├── tailwind.config.ts
├── postcss.config.js
├── next.config.mjs
├── package.json
└── tsconfig.json
```

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.
